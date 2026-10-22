# Astra答B友问：问界M9神木事故

独立答疑片，十章回应逐帧计时、端点、标尺、弧长、80刹停45米、制动灯、路缘与立柱及白车问题。

`anonymous_questions.json`保留23条实际评论/弹幕的匿名正文、来源视频及原回应语境；`anonymous_screenshots`仅含四张评论正文，已去除头像、昵称、账号和控件。原始监测记录及未处理截图不公开。

`evidence.json`记录算术输入和模型输出。80立即按9.056m/s²恒减速刹停为27.264米；约45米来自包含0.433秒制动延迟、0.25秒建立过程和简化控制的另一组仿真。评论的42.6米百零距离仅是条件算术输入，未作为已核实测试。模型质心344—393帧弧长56.978米、直线56.856米；实际米尺仍需独立校核。白车早期约45km/h已撤回，55米候选地图线尚未可靠对应两个过点时刻。

按主片README下载三层工程后：

```powershell
.venv/Scripts/python qa_episode/compose_qa.py --preview
.venv/Scripts/python qa_episode/compose_qa.py
.venv/Scripts/python validate_v82.py --qa
```

`script.json`为最终稿，`timeline.json`由已附Charon音频生成；`validation_v82.json`记录对应MP4哈希与完整解码。Argon审稿见`argon_review.json`和`argon_receipt.json`；按原资料修改其时钟方位、评论回应对象等错误，详见`editorial_final.json`。
