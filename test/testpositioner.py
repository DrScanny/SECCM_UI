from pipython import GCSDevice, datarectools, pitools

olympus= GCSDevice()
mercury= GCSDevice()

olympus.ConnectUSB(serialnum= '0125076674')
olympus.qIDN().strip()
olympus.SVO({1:1, 2:1})
olympus.FRF()
olympus.VEL({1:10, 2:10})


mercury.ConnectUSB(serialnum= '0026550002')
mercury.qIDN().strip()
mercury.SVO(1, 1)
mercury.FRF()
mercury.VEL(1,1)

print(mercury.qPOS(), mercury.qONT().values())
print(olympus.qPOS(), olympus.qONT().values())

olympus.gcsdevice.CloseConnection()
mercury.gcsdevice.CloseConnection()




