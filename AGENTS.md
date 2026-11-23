# Development requirements

- Keep input files read-only. Export must not overwrite the input or an alias to it.
- Distinguish pixel layout, bit storage, YCbCr matrix, RGB primaries, transfer function and quantization range.
- Do not claim universal raw format support. Register and document each supported layout explicitly.
- Preserve source precision; use original-resolution arrays for conversion. 8bit is only the on-screen preview.
- Run unit tests, UI smoke, and packaged smoke after relevant changes. Verify raw fixtures against analytical byte layouts.
- Do not run decoding or color conversion on the UI thread. Discard cancelled/stale jobs.
- Keep MSI UpgradeCode stable; Prism Pixel and Prism Compare must not share installer or registry identifiers.
