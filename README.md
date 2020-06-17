## API参考文档

主要的API参考文档如下：

#### from uiotedgedriverlinksdk
* **[getLogger()](#getLogger)**

---

#### from uiotedgedriverlinksdk.client
* **[getConfig()](#getConfig)**
* **[Config()](#Config)**
* Config#**[getDeviceInfos()](#getDeviceInfos)**
* Config#**[getDriverInfo()](#getDriverInfo)**


---

#### from uiotedgedriverlinksdk.exception
* BaseEdgeException
* EdgeDriverLinkException 
* EdgeDriverLinkTimeoutException
* EdgeDriverLinkDeviceConfigException
* EdgeDriverLinkDeviceOfflineException
* EdgeDriverLinkOfflineException
* EdgeDriverLinkDeviceProductSecretException


---
#### from uiotedgedriverlinksdk.client

* **[SubDevice()](#subdevice)**
* SubDevice#**[set_product_sn()](#set_product_sn)**
* SubDevice#**[set_device_sn()](#set_device_sn)**
* SubDevice#**[set_product_secret()](#set_product_secret)**
* SubDevice#**[set_msg_callback()](#set_msg_callback)**
* SubDevice#**[login()](#login)**
* SubDevice#**[logout()](#logout)**
* SubDevice#**[publish()](#publish)**
* SubDevice#**[registerDevice()](#registerDevice)**

---

#### from uiotedgedriverlinksdk.edge

* **[register_device()](#register)**
* **[set_on_topo_change_callback()](#set_on_topo_change_callback)**
* **[set_on_status_change_callback()](#set_on_status_change_callback)**
* **[get_topo()](#get_topo)**
* **[add_topo()](#add_topo)**
* **[delete_topo()](#delete_topo)**


---
* **[get_edge_online_status()](#get_edge_online_status)**

---
<a name="getLogger"></a>
### getLogger()
返回驱动内置logger。

---
<a name="getConfig"></a>
### getConfig()
返回驱动相关配置。

---
<a name="Config"></a>
### Config()
基于当前驱动配置字符串构造新的Config对象。

---
<a name="getDeviceInfos"></a>
### Config. getDeviceInfos()
返回所有设备相关信息，返回DeviceInfo`List`
DeviceInfo包括如下信息：

* productSN `str `: 官网申请的productKey。
* deviceSN `str `: 设备名
* config`dict `:设备自定义配置

---
<a name="getDriverInfo"></a>
### Config. getDriverInfo()
返回驱动相关信息，返回DriverInfo`List`

---
<a name="subdevice"></a>
### SubDevice(product_sn,device_sn, on_msg_callback)
设备接入客户端类, 用户主要通过它上下线设备和主动上报消息

* product_sn`str`: 云端分配的ProductSN
* device_sn`str`: 云端分配的DeviceSN
* on_msg_callback`func(topic:str, msg:b'')`: 云端下发消息回调，消息类型 []byte, 例如：` def callbacl(topic:str, msg:b''): print(str(msg,'utf-8')`

---
<a name="set_product_sn"></a>
### SubDevice.set_product_sn(product_sn)
设置子设备的productSN

* product_sn`str`: 云端分配的ProductSN


---
<a name="set_device_sn"></a>
### SubDevice.set_device_sn(device_sn)
设备子设备的DeviceSN

* device_sn`str`: 云端分配的DeviceSN


---
<a name="set_product_secret"></a>
### SubDevice.set_product_secret(product_secret)
设置子设备的Product Secret

* product_secret`str`: 云端分配的Product Secret


---
<a name="set_product_secret"></a>
### SubDevice.set_product_secret(product_secret)
设置子设备的Product Secret

* product_secret`str`: 云端分配的Product Secret


---
<a name="set_msg_callback"></a>
### SubDevice.set_msg_callback(msg_callback)
设置子设备的接收消息的回调函数

* set_msg_callback`func`: 子设备收消息回调，例如：` def callbacl(topic:str, msg:b''): print(str(msg,'utf-8')`


---
<a name="login"></a>
### SubDevice.login(sync=False, timeout=5)
上报上线事件到Link IoT Edge

* sync`bool`: 是否异步登陆
* timeout`int`: 等待响应超时时间，单位s(秒)

---
<a name="logout"></a>
### SubDevice.logout(sync=False, timeout=5)
上报下线事件到Link IoT Edge

* sync`bool`: 是否异步登陆
* timeout`int`: 等待响应超时时间，单位s(秒)

---
<a name="publish"></a>
### SubDevice.publish(topic, payload)
上报消息到Link IoT Edge。异步

* topic`str`: 上报消息到Link IoT Edge的mqtt topic。
* payload`[]byte`: 上报消息到Link IoT Edge的消息内容


---

<a name="registerDevice"></a>
### SubDevice.registerDevice(timeout)
动态注册一个设备到Link IoT Edge。同步

* timeout`int`: 等待响应超时时间，单位s(秒)
---


---
<a name="register"></a>
### register_device(product_sn, device_sn, product_secret, timeout=5)
上报动态注册到Link IoT Edge。同步执行，等待响应

* product_sn`str`: 云端分配的ProductSN
* device_sn`str`:  自定义的DeviceSN
* product_secret`str`: ProductSecret
* timeout`int`: 等待响应超时时间，单位s(秒)

---
<a name="set_on_topo_change_callback"></a>
### set_on_topo_change_callback(callback)
云端topo信息变化的下发消息的回调函数

* callback`func`: 云端下发消息回调，消息类型 {}, 例如： `def callback(msg): print(msg)`


---
<a name="set_on_status_change_callback"></a>
### set_on_status_change_callback(callback)
云端设备启用和禁用信息变化的下发消息的回调函数

* callback`func`: 云端下发消息回调，消息类型 {}, 例如： `def callback(msg): print(msg)`


---
<a name="get_topo"></a>
### get_topo(timeout=5)
上报get topo信息到Link IoT Edge。同步执行，等待响应

* timeout`int`: 等待响应超时时间，单位s(秒)

---
<a name="add_topo"></a>
### add_topo(product_sn, device_sn, timeout=5)
上报add topo信息到Link IoT Edge

* product_sn`str`: 云端分配的ProductSN
* device_sn`str`: 云端分配的DeviceSN
* timeout`int`: 等待响应超时时间，单位s(秒)

---
<a name="delete_topo"></a>
### delete_topo(product_sn, device_sn, timeout=5)
上报delete topo信息到Link IoT Edge

* product_sn`str`: 云端分配的ProductSN
* device_sn`str`: 云端分配的DeviceSN
* timeout`int`: 等待响应超时时间，单位s(秒)


---

<a name="get_edge_online_status"></a>
### get_edge_online_status()
获取网关的在线状态，返回True / False

---

