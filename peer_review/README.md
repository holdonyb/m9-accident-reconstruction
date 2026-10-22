# 四条视频的方法复核

新片：https://www.bilibili.com/video/BV1P7nm6fEUH/ （370.1秒，1080p30）

原仿真独立 P2：https://www.bilibili.com/video/BV1p9nC6mE12/?p=2

新片内容：原片校时与重复画面、两套标尺的距离分歧、同时间同距离而末速不同的三维控制实验、按原作者参数复算及双机位观感比较。结论与原视频时间位置见《分析结论与证据.md》。

## 下载与复现

补充 ZIP 解压在 v8.0.0 完整工程根目录中，形成 `peer_review/`。基础工程下载：https://github.com/holdonyb/m9-accident-reconstruction/releases/download/v8.0.0/M9-Blender-MuJoCo-project.zip

Python 3.11 / Blender 5.1 / FFmpeg。安装本目录 requirements.txt；字体默认 Windows 微软雅黑。已有男声 WAV 与 Blender 渲染，可以直接重新合成。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r peer_review/requirements.txt
.venv/Scripts/python peer_review/recalculate.py
.venv/Scripts/python peer_review/compose_review.py --preview
.venv/Scripts/python peer_review/compose_review.py
```

需要重做控制实验镜头时：`blender -b --python peer_review/blender_mean_demo.py`。代码中的动力学基础文件读取 v8 根目录；本补充的三辆车演示是明确指定速度函数的运动学反例，目的是说明观测不能唯一确定末速。原 P2 的十一组运动由 MuJoCo 计算，属于另一个对照层次。

合成器将每章写入 edit/；完成标记是同名 .done。修改文案、画面后删除或另存受影响章节的缓存标记再合成。保留旧稿请先复制目录。模型文件可直接在 Blender 打开。公开包中包含必要的带出处静帧，未收录他人的整条视频及音轨。

## 关键数据

- 第一条三个算式：74.25 / 58.8 / 30.52 km/h，均为区间平均值。
- 方法示例：6.5m、23/30s；减速度0/4/8m/s²；末速30.52/25.00/19.48km/h。
- 第二条给定条件：49.7—54.7m，44.5/29.8s，制动起点7.5/29.8s，0.5—0.8g。复算初速128.9—146.5、末速99.3—119.1km/h。
- 本地原片大字时钟13/14/15/16秒对应零基文件帧308/339/368/398；三秒90帧。重复画面保留时间戳。
- 白车经过时，5/6/7/8秒首次清晰可读对应连续解码68/107/128/157帧，间隔39/21/29帧；局部更新节奏不均匀，三秒总计89帧。第67帧时钟存在混合字形，逐帧证据见 clock_exact_decode.jpg。

这些数字分属原作者输入、条件模型和方法演示。白车实际速度还缺可靠的地图端点与过点时刻对应；不把旧条件模型45km/h作为实测速。

文案经 Vertex Gemini 4 Argon 审稿并按原始资料人工核对；配音为 Vertex Gemini 3.8 TTS / Charon。19段音频哈希与文本对应。
