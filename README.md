
## API参考文档

主要的API参考文档如下：

* **[getConfig()](#getConfig)**
* **[Config()](#Config)**
* Config#**[getThingInfos()](#getThingInfos)**
* Config#**[getDriverInfo()](#getDriverInfo)**

---
* **[ThingAccessClient()](#thingaccessclient)**
* ThingAccessClient#**[set_product_sn()](#set_product_sn)**
* ThingAccessClient#**[set_device_sn()](#set_device_sn)**
* ThingAccessClient#**[set_product_secret()](#set_product_secret)**
* ThingAccessClient#**[set_msg_callback()](#set_msg_callback)**
* ThingAccessClient#**[login()](#login)**
* ThingAccessClient#**[logout()](#logout)**
* ThingAccessClient#**[publish()](#publish)**

---
* **[register_device()](#register)**
* **[set_on_topo_change_callback()](#set_on_topo_change_callback)**
* **[set_on_status_change_callback()](#set_on_status_change_callback)**
* **[get_topo()](#get_topo)**
* **[add_topo()](#add_topo)**
* **[delete_topo()](#delete_topo)**


---
* **[get_edge_online_status()](#get_edge_online_status)**

---
<a name="getConfig"></a>
### getConfig()
返回驱动相关配置

---
<a name="Config"></a>
### Config()
基于当前驱动配置字符串构造新的Config对象

---
<a name="getThingInfos"></a>
### Config. getThingInfos()
返回所有设备相关信息，返回ThingInfo`List`
ThingInfo包括如下信息：

* productKey `str `: 官网申请的productKey
* deviceName `str `: 设备名
* custom`dict `:设备自定义配置

---
<a name="getDriverInfo"></a>
### Config. getDriverInfo()
返回驱动相关信息，返回DriverInfo `List`

---
<a name="thingaccessclient"></a>
### ThingAccessClient(product_sn,device_sn, on_msg_callback)
设备接入客户端类, 用户主要通过它上下线设备和主动上报消息

* product_sn`str`: 云端分配的ProductSN
* device_sn`str`: 云端分配的DeviceSN
* on_msg_callback`func(msg:b'')`: 云端下发消息回调，消息类型 []byte, 例如：` def callbacl(msg:b''): print(str(msg,'utf-8')`

---
<a name="set_product_sn"></a>
### ThingAccessClient.set_product_sn(product_sn)
设置子设备的productSN

* product_sn`str`: 云端分配的ProductSN


---
<a name="set_device_sn"></a>
### ThingAccessClient.set_device_sn(device_sn)
设置子设备的DeviceSN

* device_sn`str`: 云端分配的DeviceSN


---
<a name="set_product_secret"></a>
### ThingAccessClient.set_product_secret(product_secret)
设置子设备的Product Secret

* product_secret`str`: 云端分配的Product Secret


---
<a name="set_product_secret"></a>
### ThingAccessClient.set_product_secret(product_secret)
设置子设备的Product Secret

* product_secret`str`: 云端分配的Product Secret


---
<a name="set_msg_callback"></a>
### ThingAccessClient.set_msg_callback(msg_callback)
设置子设备的接收消息的回调函数

* set_msg_callback`func`: 子设备收消息回调


---
<a name="login"></a>
### ThingAccessClient.login()
上报上线事件到Link IoT Edge。异步

---
<a name="logout"></a>
### ThingAccessClient.logout()
上报下线事件到Link IoT Edge。异步


---
<a name="publish"></a>
### ThingAccessClient.publish(topic, payload, is_cached, duration)
上报消息到Link IoT Edge。异步

* topic`str`: 上报消息到Link IoT Edge的mqtt topic。
* payload`[]byte`: 上报消息到Link IoT Edge的消息内容
* is_cached`bool`: IOT Edge是否缓存消息
* duration`int`: IOT Edge缓存消息时间，单位s(秒)

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

* callback`func`: 云端下发消息回调，消息类型 []byte, 例如： `def callbacl(msg:b''): print(str(msg,'utf-8')`


---
<a name="set_on_status_change_callback"></a>
### set_on_status_change_callback(callback)
云端设备启用和禁用信息变化的下发消息的回调函数

* callback`func`: 云端下发消息回调，消息类型 []byte, 例如： def callbacl(msg:b''): print(str(msg,'utf-8')


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
