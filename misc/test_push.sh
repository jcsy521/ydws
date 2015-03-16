curl -i -X POST -d uid='jia355921040793778' -d key='e11e7e3e21180fd' -d body='{"comment": "", "category": 4, "region_id": -1, "degree": 321.8, "timestamp": 1398394347, "longitude": 408571920, "alias": "TE6094(\u4e16\u5149)", "tid": "CBBJTEAM01", "clongitude": 408614180, "pbat": "94", "latitude": 80247132, "clatitude": 80259048, "type": 0, "speed": 63.6, "name": "test"}'  http://192.168.108.44:8805/androidpush/push


curl -d uid=1 -d alert=1 -d badge=1  -d  body='{"category": 3, "name": "\u5317\u4eac\u5e02\u6d77\u5dc0\u533a", "degree": 0.0, "timestamp": 1354323602, "volume": "9", "alias": "\u4eaca1222", "clongitude": 418807850, "tid": "A9997JTD12A0FTXM88", "clatitude": 144001684, "type": 1, "speed": 788.0, "uid": "13693675352"}' http://192.168.1.205:8805/androidpush/iospush
