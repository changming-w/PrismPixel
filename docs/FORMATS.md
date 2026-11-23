# 格式清单

首版登记 127 种明确排布，均可读写。LE/BE 指样本字的小/大端；PLANAR 的 10/12bit 在 little-endian 16bit 字低位。TIGHT_LSB 为分量连续低位优先位流，每行独立；不是 MIPI RAW10。

| 名称 | 说明 |
| --- | --- |
| `RGB8` | RGB · 交错 · 8bit · 低位对齐 |
| `RGB10_U16LE` | RGB · 交错 · 10bit · 低位对齐 |
| `RGB10_MSB16LE` | RGB · 交错 · 10bit · 高位对齐 |
| `RGB10_U16BE` | RGB · 交错 · 10bit · 低位对齐 |
| `RGB10_MSB16BE` | RGB · 交错 · 10bit · 高位对齐 |
| `RGB12_U16LE` | RGB · 交错 · 12bit · 低位对齐 |
| `RGB12_MSB16LE` | RGB · 交错 · 12bit · 高位对齐 |
| `RGB12_U16BE` | RGB · 交错 · 12bit · 低位对齐 |
| `RGB12_MSB16BE` | RGB · 交错 · 12bit · 高位对齐 |
| `RGB16_U16LE` | RGB · 交错 · 16bit · 低位对齐 |
| `RGB16_U16BE` | RGB · 交错 · 16bit · 低位对齐 |
| `BGR8` | BGR · 交错 · 8bit · 低位对齐 |
| `BGR10_U16LE` | BGR · 交错 · 10bit · 低位对齐 |
| `BGR10_MSB16LE` | BGR · 交错 · 10bit · 高位对齐 |
| `BGR10_U16BE` | BGR · 交错 · 10bit · 低位对齐 |
| `BGR10_MSB16BE` | BGR · 交错 · 10bit · 高位对齐 |
| `BGR12_U16LE` | BGR · 交错 · 12bit · 低位对齐 |
| `BGR12_MSB16LE` | BGR · 交错 · 12bit · 高位对齐 |
| `BGR12_U16BE` | BGR · 交错 · 12bit · 低位对齐 |
| `BGR12_MSB16BE` | BGR · 交错 · 12bit · 高位对齐 |
| `BGR16_U16LE` | BGR · 交错 · 16bit · 低位对齐 |
| `BGR16_U16BE` | BGR · 交错 · 16bit · 低位对齐 |
| `RGBA8` | RGBA · 交错 · 8bit · 低位对齐 |
| `RGBA10_U16LE` | RGBA · 交错 · 10bit · 低位对齐 |
| `RGBA10_MSB16LE` | RGBA · 交错 · 10bit · 高位对齐 |
| `RGBA10_U16BE` | RGBA · 交错 · 10bit · 低位对齐 |
| `RGBA10_MSB16BE` | RGBA · 交错 · 10bit · 高位对齐 |
| `RGBA12_U16LE` | RGBA · 交错 · 12bit · 低位对齐 |
| `RGBA12_MSB16LE` | RGBA · 交错 · 12bit · 高位对齐 |
| `RGBA12_U16BE` | RGBA · 交错 · 12bit · 低位对齐 |
| `RGBA12_MSB16BE` | RGBA · 交错 · 12bit · 高位对齐 |
| `RGBA16_U16LE` | RGBA · 交错 · 16bit · 低位对齐 |
| `RGBA16_U16BE` | RGBA · 交错 · 16bit · 低位对齐 |
| `BGRA8` | BGRA · 交错 · 8bit · 低位对齐 |
| `BGRA10_U16LE` | BGRA · 交错 · 10bit · 低位对齐 |
| `BGRA10_MSB16LE` | BGRA · 交错 · 10bit · 高位对齐 |
| `BGRA10_U16BE` | BGRA · 交错 · 10bit · 低位对齐 |
| `BGRA10_MSB16BE` | BGRA · 交错 · 10bit · 高位对齐 |
| `BGRA12_U16LE` | BGRA · 交错 · 12bit · 低位对齐 |
| `BGRA12_MSB16LE` | BGRA · 交错 · 12bit · 高位对齐 |
| `BGRA12_U16BE` | BGRA · 交错 · 12bit · 低位对齐 |
| `BGRA12_MSB16BE` | BGRA · 交错 · 12bit · 高位对齐 |
| `BGRA16_U16LE` | BGRA · 交错 · 16bit · 低位对齐 |
| `BGRA16_U16BE` | BGRA · 交错 · 16bit · 低位对齐 |
| `ARGB8` | ARGB · 交错 · 8bit · 低位对齐 |
| `ARGB10_U16LE` | ARGB · 交错 · 10bit · 低位对齐 |
| `ARGB10_MSB16LE` | ARGB · 交错 · 10bit · 高位对齐 |
| `ARGB10_U16BE` | ARGB · 交错 · 10bit · 低位对齐 |
| `ARGB10_MSB16BE` | ARGB · 交错 · 10bit · 高位对齐 |
| `ARGB12_U16LE` | ARGB · 交错 · 12bit · 低位对齐 |
| `ARGB12_MSB16LE` | ARGB · 交错 · 12bit · 高位对齐 |
| `ARGB12_U16BE` | ARGB · 交错 · 12bit · 低位对齐 |
| `ARGB12_MSB16BE` | ARGB · 交错 · 12bit · 高位对齐 |
| `ARGB16_U16LE` | ARGB · 交错 · 16bit · 低位对齐 |
| `ARGB16_U16BE` | ARGB · 交错 · 16bit · 低位对齐 |
| `ABGR8` | ABGR · 交错 · 8bit · 低位对齐 |
| `ABGR10_U16LE` | ABGR · 交错 · 10bit · 低位对齐 |
| `ABGR10_MSB16LE` | ABGR · 交错 · 10bit · 高位对齐 |
| `ABGR10_U16BE` | ABGR · 交错 · 10bit · 低位对齐 |
| `ABGR10_MSB16BE` | ABGR · 交错 · 10bit · 高位对齐 |
| `ABGR12_U16LE` | ABGR · 交错 · 12bit · 低位对齐 |
| `ABGR12_MSB16LE` | ABGR · 交错 · 12bit · 高位对齐 |
| `ABGR12_U16BE` | ABGR · 交错 · 12bit · 低位对齐 |
| `ABGR12_MSB16BE` | ABGR · 交错 · 12bit · 高位对齐 |
| `ABGR16_U16LE` | ABGR · 交错 · 16bit · 低位对齐 |
| `ABGR16_U16BE` | ABGR · 交错 · 16bit · 低位对齐 |
| `RGB10_TIGHT_LSB` | 每 4 分量 5 字节 · LSB 位流 · 每行独立打包 |
| `RGB8_PLANAR` | RGB · 平面 · 8bit · 低位对齐 |
| `RGB10_PLANAR` | RGB · 平面 · 10bit · 低位对齐 |
| `RGB12_PLANAR` | RGB · 平面 · 12bit · 低位对齐 |
| `RGB16_PLANAR` | RGB · 平面 · 16bit · 低位对齐 |
| `RGB565LE` | 16bit 字：高→低 RGB = 5/6/5bit |
| `RGB565BE` | 16bit 字：高→低 RGB = 5/6/5bit |
| `BGR10_TIGHT_LSB` | 每 4 分量 5 字节 · LSB 位流 · 每行独立打包 |
| `BGR8_PLANAR` | BGR · 平面 · 8bit · 低位对齐 |
| `BGR10_PLANAR` | BGR · 平面 · 10bit · 低位对齐 |
| `BGR12_PLANAR` | BGR · 平面 · 12bit · 低位对齐 |
| `BGR16_PLANAR` | BGR · 平面 · 16bit · 低位对齐 |
| `BGR565LE` | 16bit 字：高→低 BGR = 5/6/5bit |
| `BGR565BE` | 16bit 字：高→低 BGR = 5/6/5bit |
| `RGB10A2_LE` | 32bit 字：低→高 RGBA = 10/10/10/2bit |
| `BGR10A2_LE` | 32bit 字：低→高 BGRA = 10/10/10/2bit |
| `GBR8_PLANAR` | GBR · 平面 · 8bit · 低位对齐 |
| `GBR16_PLANAR` | GBR · 平面 · 16bit · 低位对齐 |
| `I420` | 4:2:0 · 平面 · 8bit · 低位对齐 |
| `YV12` | 4:2:0 · 平面 · 8bit · 低位对齐 |
| `I422` | 4:2:2 · 平面 · 8bit · 低位对齐 |
| `I444` | 4:4:4 · 平面 · 8bit · 低位对齐 |
| `YUV420P10LE` | 4:2:0 · 平面 · 10bit · 低位对齐 |
| `YUV420P10BE` | 4:2:0 · 平面 · 10bit · 低位对齐 |
| `YUV420P12LE` | 4:2:0 · 平面 · 12bit · 低位对齐 |
| `YUV420P12BE` | 4:2:0 · 平面 · 12bit · 低位对齐 |
| `YUV420P16LE` | 4:2:0 · 平面 · 16bit · 低位对齐 |
| `YUV420P16BE` | 4:2:0 · 平面 · 16bit · 低位对齐 |
| `YUV422P10LE` | 4:2:2 · 平面 · 10bit · 低位对齐 |
| `YUV422P10BE` | 4:2:2 · 平面 · 10bit · 低位对齐 |
| `YUV422P12LE` | 4:2:2 · 平面 · 12bit · 低位对齐 |
| `YUV422P12BE` | 4:2:2 · 平面 · 12bit · 低位对齐 |
| `YUV422P16LE` | 4:2:2 · 平面 · 16bit · 低位对齐 |
| `YUV422P16BE` | 4:2:2 · 平面 · 16bit · 低位对齐 |
| `YUV444P10LE` | 4:4:4 · 平面 · 10bit · 低位对齐 |
| `YUV444P10BE` | 4:4:4 · 平面 · 10bit · 低位对齐 |
| `YUV444P12LE` | 4:4:4 · 平面 · 12bit · 低位对齐 |
| `YUV444P12BE` | 4:4:4 · 平面 · 12bit · 低位对齐 |
| `YUV444P16LE` | 4:4:4 · 平面 · 16bit · 低位对齐 |
| `YUV444P16BE` | 4:4:4 · 平面 · 16bit · 低位对齐 |
| `NV12` | 4:2:0 · 半平面 · 8bit · 低位对齐 |
| `NV21` | 4:2:0 · 半平面 · 8bit · 低位对齐 |
| `NV16` | 4:2:2 · 半平面 · 8bit · 低位对齐 |
| `NV61` | 4:2:2 · 半平面 · 8bit · 低位对齐 |
| `NV24` | 4:4:4 · 半平面 · 8bit · 低位对齐 |
| `NV42` | 4:4:4 · 半平面 · 8bit · 低位对齐 |
| `P010` | 4:2:0 · 半平面 · 10bit · 高位对齐 |
| `P012` | 4:2:0 · 半平面 · 12bit · 高位对齐 |
| `P016` | 4:2:0 · 半平面 · 16bit · 低位对齐 |
| `P210` | 4:2:2 · 半平面 · 10bit · 高位对齐 |
| `P212` | 4:2:2 · 半平面 · 12bit · 高位对齐 |
| `P216` | 4:2:2 · 半平面 · 16bit · 低位对齐 |
| `P410` | 4:4:4 · 半平面 · 10bit · 高位对齐 |
| `P412` | 4:4:4 · 半平面 · 12bit · 高位对齐 |
| `P416` | 4:4:4 · 半平面 · 16bit · 低位对齐 |
| `YUYV` | 4:2:2 · 交错 · 8bit · 低位对齐 |
| `UYVY` | 4:2:2 · 交错 · 8bit · 低位对齐 |
| `YVYU` | 4:2:2 · 交错 · 8bit · 低位对齐 |
| `VYUY` | 4:2:2 · 交错 · 8bit · 低位对齐 |
| `Y210` | 4:2:2 · 交错 · 10bit · 高位对齐 |
| `Y216` | 4:2:2 · 交错 · 16bit · 低位对齐 |
