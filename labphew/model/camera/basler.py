"""
    Basler Camera Model
    ===================
    Model to adapt PyPylon to the needs of PyNTA. PyPylon is only a wrapper for Pylon, thus the documentation
    has to be found in the folder where Pylon was installed. It refers only to the C++ documentation, which is
    very extensive, but not necessarily clear.

    Some assumptions
    ----------------
    The program forces software trigger during :meth:`~experimentor.model.cameras.basler.Camera.initialize`.
"""
import logging
import time
from multiprocessing import Event
from threading import Lock
from typing import Tuple

import numpy as np
from dispertech.models.cameras import _basler_lock
from dispertech.util.log import get_logger
from experimentor import Q_
from experimentor.core.pusher import Pusher
from experimentor.models.cameras.base_camera import BaseCamera
from experimentor.models.cameras.exceptions import CameraNotFound, WrongCameraState
from experimentor.models.decorators import make_async_thread
from experimentor.models.properties import Properties
from pypylon import pylon, _genicam


class Camera(BaseCamera):
    def __init__(self, camera):
        super().__init__(camera)
        self.logger = get_logger(__name__)
        self.cam_num = camera
        self.max_width = 0
        self.max_height = 0
        self.width = None
        self.height = None
        self.mode = None
        self.X = None
        self.Y = None
        self.friendly_name = None
        self._stop_free_run = Event()
        self.free_run_running = False
        self.pusher = Pusher()
        self.fps = 0
        self.i = 0  # Number of frames acquired
        self.gain = 0
        self.exposure = Q_('.1s')
        self.camera = None
        self.initialize_lock = Lock()  # Lock used to prevent anything from happening before initializing the camera

        self.config = Properties.from_dict(self, data={
            'exposure': [Q_('.1s'), 'get_exposure', 'set_exposure'],
            'gain': [0, 'get_gain', 'set_gain'],
            'offset_x': [0, 'camera.OffsetX.GetValue', None]
        })

    def initialize(self):
        """ Initializes the communication with the camera. Get's the maximum and minimum width. It also forces
        the camera to work on Software Trigger.

        .. warning:: It may be useful to integrate other types of triggers in applications that need to
            synchronize with other hardware.

        """
        with self.initialize_lock:
            self.logger.debug(f'Initializing Basler Camera {self.cam_num}')
            tl_factory = pylon.TlFactory.GetInstance()
            devices = tl_factory.EnumerateDevices()
            if len(devices) == 0:
                raise CameraNotFound('No camera found')

            for device in devices:
                if str(self.cam_num) in device.GetFriendlyName():
                    self.camera = pylon.InstantCamera()
                    self.camera.Attach(tl_factory.CreateDevice(device))
                    self.camera.Open()
                    self.friendly_name = device.GetFriendlyName()

            if not self.camera:
                msg = f'{self.cam_num} not found. Please check your config file and cameras connected'
                self.logger.error(msg)
                raise CameraNotFound(msg)

            self.logger.info(f'Loaded camera {self.camera.GetDeviceInfo().GetModelName()}')

            self.camera.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll,
                                              pylon.Cleanup_Delete)
            self.clear_ROI()
            self.max_width = self.camera.Width.Max
            self.max_height = self.camera.Height.Max
            offsetX = self.camera.OffsetX.Value
            offsetY = self.camera.OffsetY.Value
            width = self.camera.Width.Value
            height = self.camera.Height.Value
            self.X = (offsetX, offsetX + width)
            self.Y = (offsetY, offsetY + height)
            self.set_acquisition_mode(self.MODE_SINGLE_SHOT)

            self.exposure = self.get_exposure()
            self.gain = self.get_gain()

    def set_acquisition_mode(self, mode):
        if self._camera.IsGrabbing():
            self.logger.warning(f'{self.friendly_name} Changing acquisition mode for a grabbing camera')

        self.logger.info(f'{self.friendly_name} Setting acquisition mode to {mode}')
        if mode == self.MODE_CONTINUOUS:
            self.logger.debug(f'Setting buffer to {self.camera.MaxNumBuffer.Value}')
            self.mode = mode
        elif mode == self.MODE_SINGLE_SHOT:
            self.logger.debug(f'Setting buffer to 1')
            self.mode = mode
        # self.logger.info('Starting Acquisition')
        # self.camera.AcquisitionStart.Execute()

    def auto_exposure(self):
        self.camera.ExposureAuto.SetValue('Off')
        self.camera.ExposureAuto.SetValue('Once')
        self.get_exposure()

    def set_auto_exposure(self, mode: str):
        """Set auto exposure. Possible modes are Off, Once, Continuous"""
        possible_modes = ('Off', 'Once', 'Continuous')
        if mode not in possible_modes:
            raise ValueError(f'Mode must be one of {possible_modes} and not {mode}')

        self.camera.ExposureAuto.SetValue(mode)

    def set_auto_gain(self, mode: str):
        """Set the auto gain. Possible modes are Off, Once, Continuous"""
        possible_modes = ('Off', 'Once', 'Continuous')
        if mode not in possible_modes:
            raise ValueError(f'Mode must be one of {possible_modes} and not {mode}')
        self.camera.GainAuto.SetValue(mode)

    def auto_gain(self):
        self.camera.GainAuto.SetValue('Off')
        self.camera.GainAuto.SetValue('Once')
        self.get_gain()

    def set_ROI(self, X: Tuple[int, int], Y: Tuple[int, int]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """ Set up the region of interest of the camera. Basler calls this the
        Area of Interest (AOI) in their manuals. Beware that not all cameras allow
        to set the ROI (especially if they are not area sensors).
        Both the corner positions and the width/height need to be multiple of 4.
        Compared to Hamamatsu, Baslers provides a very descriptive error warning.

        :param tuple X: Horizontal limits for the pixels, 0-indexed and including the extremes. You can also check
            :mod:`Base Camera <pynta.model.cameras.base_camera>`
            To select, for example, the first 100 horizontal pixels, you would supply the following: (0, 99)
        :param tuple Y: Vertical limits for the pixels.
        """
        self._stop_free_run.set()
        while self.free_run_running:
            self.logger.info('Changing ROI while free running')
            time.sleep(0.002)

        width = int(X[1] - X[1] % 4)
        x_pos = int(X[0] - X[0] % 4)
        height = int(Y[1] - Y[1] % 2)
        y_pos = int(Y[0] - Y[0] % 2)
        self.logger.info(f'Updating ROI: (x, y, width, height) = ({x_pos}, {y_pos}, {width}, {height})')
        # if x_pos+width-1 > self.max_width:
        #     raise CameraException('ROI width bigger than camera area')
        # if y_pos+height-1 > self.max_height:
        #     raise CameraException('ROI height bigger than camera area')

        # First set offset to minimum, to avoid problems when going to a bigger size
        self.clear_ROI()
        self.logger.debug(f'Setting width to {width}')
        self.camera.Width.SetValue(width)
        self.logger.debug(f'Setting Height to {height}')
        self.camera.Height.SetValue(height)
        self.logger.debug(f'Setting X offset to {x_pos}')
        self.camera.OffsetX.SetValue(x_pos)
        self.logger.debug(f'Setting Y offset to {y_pos}')
        self.camera.OffsetY.SetValue(y_pos)
        self.X = (x_pos, x_pos + width)
        self.Y = (y_pos, y_pos + width)
        self.width = self.camera.Width.Value
        self.height = self.camera.Height.Value
        return (x_pos, width), (y_pos, height)

    def clear_ROI(self):
        """ Resets the ROI to the maximum area of the camera"""
        self.camera.OffsetX.SetValue(self.camera.OffsetX.Min)
        self.camera.OffsetY.SetValue(self.camera.OffsetY.Min)
        self.camera.Width.SetValue(self.camera.Width.Max)
        self.camera.Height.SetValue(self.camera.Height.Max)

    def get_size(self) -> Tuple[int, int]:
        """ Get the size of the current Region of Interest (ROI). Remember that the actual size may be different from
        the size that the user requests, given that not all cameras accept any pixel. For example, Basler has some
        restrictions regarding corner pixels and possible widths.

        :return tuple: (Width, Height)
        """
        return self.camera.Width.Value, self.camera.Height.Value

    def trigger_camera(self):
        if self.camera.IsGrabbing():
            self.logger.warning('Triggering an already grabbing camera')
        self.logger.info('Stopping camera')
        self.camera.StopGrabbing()
        if self.mode == self.MODE_CONTINUOUS:
            self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
            self.logger.info('Setting grab strategy to one by one')
        elif self.mode == self.MODE_SINGLE_SHOT:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.logger.info('Setting grab strategy to Latest Image Only')
        self.camera.ExecuteSoftwareTrigger()
        self.logger.info('Executed Software Trigger')

    def set_gain(self, gain: float) -> float:
        self.logger.info(f'Setting gain to {gain}')
        try:
            self.camera.Gain.SetValue(gain)
        except _genicam.RuntimeException:
            self.logger.error('Problem setting the gain')
        return self.get_gain()

    def get_gain(self) -> float:
        try:
            self.gain = float(self.camera.Gain.Value)
            return self.gain
        except _genicam.TimeoutException:
            return self.gain

    def set_exposure(self, exposure: Q_) -> Q_:
        self.logger.info('Setting exposure to {:~}'.format(exposure))
        try:
            self.camera.ExposureTime.SetValue(exposure.m_as('us'))
        except _genicam.RuntimeException:
            self.logger.error('Problem setting the exposure')
        return self.get_exposure()

    def get_exposure(self) -> Q_:
        try:
            self.exposure = float(self.camera.ExposureTime.ToString()) * Q_('us')
            return self.exposure
        except _genicam.TimeoutException:
            return self.exposure

    def read_camera(self) -> list:
        with _basler_lock:
            img = []
            if self.mode == self.MODE_SINGLE_SHOT:
                grab = self.camera.RetrieveResult(int(self.exposure.m_as('ms')) + 100, pylon.TimeoutHandling_Return)
                if grab and grab.GrabSucceeded():
                    img = [grab.GetArray().T]
                grab.Release()
                self.camera.StopGrabbing()
            else:
                if not self.camera.IsGrabbing():
                    raise WrongCameraState('You need to trigger the camera before reading from it')
                num_buffers = self.camera.NumReadyBuffers.Value
                self.logger.debug(f'{num_buffers} frames available')
                if num_buffers:
                    img = [None] * num_buffers
                    for i in range(num_buffers):
                        grab = self.camera.RetrieveResult(int(self.exposure.m_as('ms'))*2, pylon.TimeoutHandling_Return)
                        skipped_frames = grab.GetNumberOfSkippedImages()
                        if skipped_frames>0:
                            self.logger.warning(f'There are {skipped_frames} skipped frames')

                        if grab and grab.GrabSucceeded():
                            img[i] = grab.GetArray().T
                        grab.Release()
            if len(img) >= 1:
                self.temp_image = img[-1]
            return img

    @make_async_thread
    def start_free_run(self):
        """ Starts continuous acquisition from the camera, but it is not being saved. This method is the workhorse
               of the program. While this method runs on its own thread, it will broadcast the images to be consumed by other
               methods. In this way it is possible to continuously save to hard drive, track particles, etc.
               """
        if self.free_run_running:
            self.logger.info(f'Trying to start again the free acquisition of camera {self}')
            return
        self.logger.info(f'Starting a free run acquisition of camera {self}')
        self.i = 0  # Used to keep track of the number of frames
        self._stop_free_run.clear()
        t0 = time.time()
        self.free_run_running = True
        self.logger.debug('First frame of a free_run')
        self.set_acquisition_mode(self.MODE_CONTINUOUS)
        self.trigger_camera()  # Triggers the camera only once
        exposure = self.get_exposure()
        try:
            while not self._stop_free_run.is_set():
                time.sleep(exposure.m_as('s'))
                data = self.read_camera()
                if not data:
                    continue
                self.logger.debug('Got {} new frames'.format(len(data)))
                img = None
                for img in data:
                    self.i += 1
                    self.logger.debug('Number of frames: {}'.format(self.i))
                    self.pusher.publish(img, f'{self.id}_free_run')
                self.fps = round(self.i / (time.time() - t0))
        except Exception as e:
            self.free_run_running = False
            self.stop_camera()
            raise
        self.free_run_running = False
        self.stop_camera()

    def stop_free_run(self):
        if self.free_run_running:
            self.logger.info('Stopping a free run')
        else:
            self.logger.info('Free run not running but stopping it')
        self._stop_free_run.set()
        time.sleep(0.005)
        t0 = time.time()
        while self.free_run_running:
            time.sleep(0.005)

    def stop_camera(self):
        self.logger.info('Stopping camera')
        self.camera.StopGrabbing()
        self.camera.AcquisitionStop.Execute()

    @property
    def id(self):
        return id(self)

    def set_pixel_format(self, format):
        self.logger.info(f'Setting pixel format to {format}')
        self.camera.PixelFormat = format

    def finalize(self):
        self.logger.debug('Finalizing camera')
        self.stop_free_run()
        while self.free_run_running:
            time.sleep(.005)
        self.stop_camera()
        self.clean_up_threads()
        if len(self._threads) > 0:
            self.logger.warning(f'There are {len(self._threads)} threads still alive in {self.friendly_name}')
            time.sleep(1)
            self.finalize()
        self.logger.info('Finalized Camera')
        super().finalize()

    def resulting_frame_rate(self):
        return self.camera.ResultingFrameRate.GetValue()

    def __str__(self):
        if self.friendly_name:
            return self.friendly_name
        return "Basler Camera"


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('Starting Basler')
    basler = Camera('pu')
    basler.initialize()
    basler.set_acquisition_mode(basler.MODE_SINGLE_SHOT)
    basler.set_exposure(Q_('.02s'))
    basler.trigger_camera()
    print(len(basler.read_camera()))
    basler.set_acquisition_mode(basler.MODE_CONTINUOUS)
    basler.trigger_camera()
    time.sleep(1)
    imgs = basler.read_camera()
    print(len(imgs))
    for img in imgs:
        plt.imshow(np.sum(img, 0))
        plt.show()
