# T480 transport

This clean-room component validates a bounded SSH target for fixed T480
operations. It does not open a connection or accept arbitrary shell commands.
Application adapters own their reviewed operation catalogue and use a fake
transport by default in tests.
