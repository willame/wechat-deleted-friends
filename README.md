# wechat-deleted-friends
查看被删的微信好友

原理就是新建群组,如果加不进来就是被删好友了(不要在群组里讲话,别人是看不见的)

用的是微信网页版的接口

查询结果可能会引起一些心理上的不适,请小心使用..(逃

还有些小问题:

结果好像有疏漏一小部分,原因不明..

最终会遗留下一个只有自己的群组,需要手工删一下

没试过被拉黑的情况

Mac OS用法:
启动Terminal

`$ python wdf.py`

按指示做即可


## 微信流程

1. jslogin 获取 uuid

    简化版 url: `https://login.weixin.qq.com/jslogin?appid=wx782c26e4c19acffb`

    返回: `window.QRLogin.code = 200; window.QRLogin.uuid = "IcBKe40AYg==";`

2. 根据 uuid 获取 qrcode

    url: `https://login.weixin.qq.com/qrcode/IcBKe40AYg==`
