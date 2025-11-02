Our goal is to provide the Python scripts required here: https://github.com/indilib/indi/blob/master/drivers/dome/dome_script.cpp#L69-79

The scripts must adhere to any design requirements and testing protocol from INDI, INDI Dome Scripting Gateway, or INDI Dome Drivers.

The scripts will be developed in Python.
The development environment is Mac, and has no access to the physical k8055 hardware.
The production environment is Raspberry Pi, and connects via USB cable to the k8055  (which in-turn controls the physical dome motors and sensors).
The (external to this project) `libk8055` dynamically-linked library only exists on the Raspberry Pi, and is incompatible with Mac.
The Python library exposed by this DLL exposes a set of functions.
`indi_k8055_dome_driver` shall wrap/abstract those functions, so full mock testing can be performed on the Mac, without needing the DLL.
