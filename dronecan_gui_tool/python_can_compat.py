#
# Compatibility fixes for pydronecan + python-can 4.4+ (PCAN, SocketCAN, ...).
#
# Upstream pydronecan still:
#   1. Calls Bus.flush_tx_buffer() which raises NotImplementedError on PCAN
#      (python-can >= 4.4). That breaks all TX.
#   2. Passes recv() timeout in milliseconds. python-can expects seconds, so
#      the GUI appears to freeze on startup (spin(0.1) waits 100 s).
#
# See: https://github.com/dronecan/pydronecan/pull/78
#      https://github.com/dronecan/pydronecan/issues/79
#

from logging import getLogger

logger = getLogger(__name__)


def apply_python_can_compat():
    try:
        from dronecan.driver.python_can import PythonCAN
    except Exception:
        logger.debug('python-can / pydronecan PythonCAN not available', exc_info=True)
        return

    if PythonCAN is None:
        return
    if getattr(PythonCAN, '_gui_tool_compat_applied', False):
        return

    _orig_init = PythonCAN.__init__

    def _patched_init(self, channel, **extras):
        _orig_init(self, channel, **extras)
        orig_flush = self._bus.flush_tx_buffer

        def _safe_flush():
            try:
                orig_flush()
            except NotImplementedError:
                pass

        self._bus.flush_tx_buffer = _safe_flush

    def _patched_receive(self, timeout=None):
        # python-can Bus.recv() takes seconds (or None), not milliseconds.
        self._check_write_feedback()
        try:
            msg = self._bus.recv(timeout=timeout)
            if msg is None:
                return None

            import time
            from dronecan.driver.common import CANFrame

            ts_mono = time.monotonic()
            ts_real = time.time()
            if ts_real and not ts_mono:
                ts_mono = self._convert_real_to_monotonic(ts_real)

            frame = CANFrame(
                msg.arbitration_id,
                msg.data,
                bool(getattr(msg, 'is_extended_id', True)),
                ts_monotonic=ts_mono,
                ts_real=ts_real,
                canfd=bool(getattr(msg, 'is_fd', False)),
            )
            self._rx_hook(frame)
            return frame
        except Exception:
            logger.error('Receive exception', exc_info=True)
            return None

    PythonCAN.__init__ = _patched_init
    PythonCAN.receive = _patched_receive
    PythonCAN._gui_tool_compat_applied = True
    logger.info('Applied python-can compatibility patches (PCAN TX/RX)')
