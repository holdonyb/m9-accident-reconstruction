# 都是逐帧算的，为什么结果不同？

问界M9神木事故四条视频的方法复核。本轮重剪补充原始输入审计、卫星图21.2米对照、透视演示和六组连续速度曲线。
B站观看入口：https://www.bilibili.com/video/BV1P7nm6fEUH/ 。上一期与十一组物理假设P2：https://www.bilibili.com/video/BV1p9nC6mE12/?p=2 。

## 先看哪些文件

- `teacher_input_audit/audit_report.html`：输入审计与交互敏感性计算。
- `teacher_input_audit/assumption_ledger.json`：13项输入与证据。
- `teacher_input_audit/frame_matches.json`：作者展示帧与本地原帧的背景配准、候选匹配及矩阵。
- `teacher_input_audit/endpoint_audit.jpg`：灯带、车尾下缘与停止线并排核对。
- `author_hypotheses.json`：六组连续曲线，各样本物理时间、位置、速度和加速度。
- `作者条件_六组速度时序对照_v3.blend`：六场景；`author_v3_validation.json`记录306个烘焙点及打包贴图检查。
- `script.json`、`timeline.json`、`validation_v82.json`：最终口播、实际音频时间轴及对应成片哈希。

## 本轮核验

作者显示的53、54帧都最佳匹配本地339；57、61匹配342、346。这表明起点展示有一帧歧义，可能是讲解编号与画面不同步，不能直接证明实际间隔必为7/30秒。

作者61帧圈选位于灯带，原片346可见车尾下缘仍在停止线近侧，并叠有两次车辆影像。因此“车尾地面过线”的事件选择需要重查。5.5米依赖三米箭头及投影标定，尚缺独立地面尺度验证。固定5.5米，7/8/9个文件帧间隔给出84.86/74.25/66 km/h，超出作者同时列出的±10%范围；这是输入敏感性，不是新的事故实测速。

卫星图56米是入口附近至对侧路缘附近的候选线。21.2米叠画在同一起点用于比较终点位置，不能直接拿56米除以作者计时。附近道路公开设计图支持当地存在三米箭头，但不证明事发路口箭头尺寸。

铂金小鸟给定49.7—54.7米、44.5/29.8秒、制动7.5/29.8秒及0.5—0.8g，复算初速128.9—146.5、末速99.3—119.1 km/h。结果随端点、车长投影和制动假设变化。厂家数值未作为本轮曲线拟合目标。

六组演示共用本地346较远灯带影像作为起点；两次曝光时刻仍有歧义。第二位作者的回放也使用该共同起点，并未独立确认其原始起点。相机米尺沿用条件标定，整套对照同时检验几何与运动假设。运动终点的速度不自动等于与柱子接触的速度。

## 复现

依次下载v8.0.0基础工程、v8.1.0补充包和v8.2.0补充包，解压到同一目录。完整视频、音频、必要引用片段、贴图和Blender文件在Releases；Git保留代码及数据，未打包其他作者完整视频。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r peer_review/requirements.txt
.venv/Scripts/python peer_review/recalculate.py
.venv/Scripts/python peer_review/author_hypotheses.py
.venv/Scripts/python peer_review/compose_review.py --preview
.venv/Scripts/python peer_review/compose_review.py
.venv/Scripts/python validate_v82.py --main
```

环境：Blender5.1、Python3.11、FFmpeg、Windows微软雅黑。已附Charon男声与文本哈希，无需再次请求Vertex。改口播后须重新配音。修改章节或画面后移走`edit_revision`中相应`.done`缓存标记，再重渲染。

重新烘焙：`blender -b --python peer_review/blender_author_replay.py`；校验：`blender -b --python peer_review/validate_author_v3.py`。306张图位于`renders_author_v3`；每组1—51帧对应时间0—T，包含两端。

文案经Vertex Gemini4 Argon审阅，再按原资料修正扩写和不实新增，取舍见`editorial_final_inputs.json`。配音为Vertex Gemini3.8 TTS / Charon。
