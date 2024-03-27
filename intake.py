from commands2 import Subsystem, Command, cmd
from phoenix5 import TalonSRX, TalonSRXControlMode
from wpilib import SmartDashboard, AnalogInput, RobotBase,Compressor
from wpilib.simulation import AnalogInputSim
import wpilib

import constants

class Intake(Subsystem):
    def __init__(self, test_mode=False):
        super().__init__()


        self.IntakedoubleSolenoid = wpilib.DoubleSolenoid(
            moduleType=wpilib.PneumaticsModuleType.CTREPCM,
            forwardChannel=2,
            reverseChannel=3,
        )

        # True has arms closed
        clawOpen = False
        if clawOpen:
            self.IntakedoubleSolenoid.set(wpilib.DoubleSolenoid.Value.kForward)
        else:
            self.IntakedoubleSolenoid.set(wpilib.DoubleSolenoid.Value.kReverse)


        self._leftGripper = TalonSRX(constants.LEFT_GRIPPER)
        self._leftGripper.configFactoryDefault()
        self._rightGripper = TalonSRX(constants.RIGHT_GRIPPER)
        self._rightGripper.configFactoryDefault()

    def drive_intakeMotors(self, intake_motor_speed):
        intake_motor_speed =  intake_motor_speed  ## Limit speed of intake
        print ("intake_motor_speed: ", intake_motor_speed)


        self._leftGripper.set(TalonSRXControlMode.PercentOutput, intake_motor_speed)
        self._rightGripper.set(TalonSRXControlMode.PercentOutput, -intake_motor_speed)

    def stop_intakeMotors(self) -> None:
        self._leftGripper.set(TalonSRXControlMode.PercentOutput, 0)
        self._rightGripper.set(TalonSRXControlMode.PercentOutput, 0)



class IntakeCommand(Command):
    """
    Command to run motors of the shooter with a button press
    """

    def __init__(self, intake: Intake):
        super().__init__()
        self._speed = 0
        self._sub = intake

        self.addRequirements(self._sub)

    def initialize(self):
        # self._speed = SmartDashboard.getNumber("IntakeSpeed", 0.3)
        pass

    def execute(self):
        self._sub.drive_intakeMotors(0.0)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self._sub.stop_intakeMotors()


class PulseIntakeMotorCommand(Command):
    """
    Command to run the intake motor for X seconds
    """

    def __init__(self, intake: Intake, pulseTime: int, speed: float):
        super().__init__()
        self._sub = intake
        self._speed = speed
        self._pulseTime = pulseTime

        self.addRequirements(self._sub)

    def initialize(self):
        self._counter = self._pulseTime * 50 ## Number of passes thru execution

    def execute(self):
        self._sub.drive_intakeMotors(self._speed)
        self._counter = self._counter - 1
        print ("Counter:  ", self._counter)

    def isFinished(self) -> bool:
        return (self._counter < 0)

    def end(self, interrupted: bool):
        self._sub.stop_intakeMotors()

