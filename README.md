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

3. 监听 qrcode 扫描结果

    url: `https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?uuid=%s&tip=0&_=timestamp_ms`

    在 response 的 body 中解析 window.code

    - 监听中, 返回 408
    - 已扫描, 等待手机确认, 返回 201
    - 手机端已确认, 返回 200, 并携带 `redirect_uri`
    - 发送 request 时, uuid 不能作为 http body 用 urlencode 处理. 否则 uuid 中的 == 会被转义, 服务端返回 500

4. POST 访问 `redirect_uri` 登录

    必须发 POST 消息, 返回 301, body 是一个 xml. 再跳转一次即可.

    若发 GET 消息, 返回 200, 回到扫二维码登录的首页

    返回 301 时, body 是 xml

        <error>
            <ret>0</ret>
            <message>OK</message>
            <skey>xxx</skey>
            <wxsid>xxx</wxsid>
            <wxuin>xxx</wxuin>
            <pass_ticket>xxx</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
