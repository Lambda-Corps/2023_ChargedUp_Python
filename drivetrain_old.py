import math

#####
import ntcore
#####

import wpilib.drive
from wpilib import RobotBase
from wpimath.controller import PIDController
from commands2 import Subsystem, Command, cmd, InstantCommand
from phoenix6.configs import (
    TalonFXConfiguration,
    TalonFXConfigurator,
    MotionMagicConfigs,
    Slot0Configs,
)
from phoenix6.hardware.talon_fx import TalonFX
from phoenix6.controls.follower import Follower
from phoenix6.signals.spn_enums import (
    InvertedValue,
    NeutralModeValue,
    FeedbackSensorSourceValue,
    MotionMagicIsRunningValue,
    ControlModeValue,
)
from phoenix6.sim import ChassisReference
from phoenix6.controls import (
    DutyCycleOut,
    VoltageOut,
    MotionMagicVoltage,
)
import navx

import constants


class DriveTrain(Subsystem):
    def __init__(self) -> None:
        super().__init__()
        self._gyro = navx.AHRS.create_spi()
        self.rangefinder1 = wpilib.AnalogInput(1)


        # Create the output objects for the talons, currently one each for
        # the following modes: VoltageOut, PercentOutput, and MotionMagic
        self.__create_output_objects()

        # Create the PID controller setup for turning
        self.__create_turn_pid_objects()

        # Apply all the configurations to the left and right side Talons
        self.__configure_left_side_drive()
        self.__configure_right_side_drive()

        ####
        self.NT_table_instance = ntcore.NetworkTableInstance.getDefault()
        self.datatable = self.NT_table_instance.getTable("photonvision/USB_Camera_1")
        self.camera_has_target = self.datatable.getBooleanTopic("hasTarget").subscribe(0)
        self.yaw_angle_to_target = self.datatable.getFloatTopic("targetYaw").subscribe(0)
        self.NT_table_instance.startClient4("Example Client")
        self.NT_table_instance.setServerTeam(1895)
        self.NT_table_instance.startDSClient()
        ###

    def __configure_motion_magic(self, config: TalonFXConfiguration) -> None:
        self._mm_setpoint = 0

        self._mm_tolerance = (
            math.pi * constants.DT_WHEEL_DIAMETER
        ) / 50  # end within 1/50th of a rotation
        config.motion_magic.motion_magic_cruise_velocity = (
            10  # 1 rps = 1.5 fps, 10 rps = 15 fps
        )
        config.motion_magic.motion_magic_acceleration = (
            20  # .5 seconds to reach full speed
        )

        # Motion Magic slot will be 0
        slot_0: Slot0Configs = config.slot0
        if RobotBase.isSimulation():
            slot_0.k_p = 1.2  # 1 full wheel rotation will correct with 1.2v power
            slot_0.k_s = 0.01  # 1 percent maybe accounts for friction?
        else:
            # TODO -- Tune these on the robot
            slot_0.k_p = 12  # 1 full wheel rotation will correct with 12 volts
            slot_0.k_s = 0

    def __create_output_objects(self) -> None:
        self._left_volts_out: VoltageOut = VoltageOut(0, enable_foc=False)
        self._left_volts_out.update_freq_hz = 0
        self._right_volts_out: VoltageOut = VoltageOut(0, enable_foc=False)
        self._right_volts_out.update_freq_hz = 0

        self._left_percent_out: DutyCycleOut = DutyCycleOut(0, enable_foc=False)
        self._right_percent_out: DutyCycleOut = DutyCycleOut(0, enable_foc=False)

        self._mm_out: MotionMagicVoltage = MotionMagicVoltage(0, enable_foc=False)

    def __create_turn_pid_objects(self) -> None:
        self._turn_setpoint = 0
        self._turn_tolerance = 0.5  # within 3 degrees we'll call good enough
        if RobotBase.isSimulation():
            self._turn_pid_controller: PIDController = PIDController(0.00175, 0.0, 0.0)
            self._turn_kF = 0.049
        else:
            # These must be tuned
            self._turn_pid_controller: PIDController = PIDController(0, 0, 0)
            self._turn_kF = 0.1  # TODO Tune me

    def __configure_left_side_drive(self) -> None:
        self._left_leader = TalonFX(constants.DT_LEFT_LEADER)
        # self._left_follower = TalonFX(constants.DT_LEFT_FOLLOWER)
        # Applying a new configuration will erase all other config settings since we start with a blank config
        # so each setting needs to be explicitly set here in the config method
        config = TalonFXConfiguration()

        # Set the left side motors to be counter clockwise positive
        config.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
        # Set the motors to electrically stop instead of coast
        config.motor_output.neutral_mode = NeutralModeValue.BRAKE
        # PID controls will use integrated encoder
        config.feedback.feedback_sensor_source = FeedbackSensorSourceValue.ROTOR_SENSOR

        config.feedback.sensor_to_mechanism_ratio = constants.DT_GEAR_RATIO

        # Configure the motion magic objects and store them as member variables
        self.__configure_motion_magic(config)

        # Apply the configuration to the motors
        self._left_leader.configurator.apply(config)
        # self._left_follower.configurator.apply(config)

        # self._left_follower.set_control(Follower(self._left_leader.device_id, False))
        self._left_leader.sim_state.Orientation = ChassisReference.Clockwise_Positive
        # self._left_follower.sim_state.Orientation = (
        #     ChassisReference.Clockwise_Positive
        # )

    def __configure_right_side_drive(self) -> None:
        self._right_leader = TalonFX(constants.DT_RIGHT_LEADER)
        # self._right_follower = TalonFX(constants.DT_LEFT_FOLLOWER)
        # Applying a new configuration will erase all other config settings since we start with a blank config
        # so each setting needs to be explicitly set here in the config method
        config = TalonFXConfiguration()

        # Set the left side motors to be counter clockwise positive
        config.motor_output.inverted = InvertedValue.COUNTER_CLOCKWISE_POSITIVE
        # Set the motors to electrically stop instead of coast
        config.motor_output.neutral_mode = NeutralModeValue.BRAKE
        # PID controls will use integrated encoder
        config.feedback.feedback_sensor_source = FeedbackSensorSourceValue.ROTOR_SENSOR

        # Configure the motion magic objects and store them as member variables
        self.__configure_motion_magic(config)

        config.feedback.sensor_to_mechanism_ratio = constants.DT_GEAR_RATIO
        # Apply the configuration to the motors
        self._right_leader.configurator.apply(config)
        # self._right_follower.configurator.apply(config)

        # self._right_follower.set_control(Follower(self._right_leader.device_id, False))
        self._right_leader.sim_state.Orientation = (
            ChassisReference.CounterClockwise_Positive
        )
        # self._right_follower.sim_state.Orientation = ChassisReference.CounterClockwise_Positive

    def drive_teleop(self, forward: float, turn: float) -> None:
        turn = self.__deadband(turn, 0.05)
        forward = self.__deadband(forward, 0.05)

        speeds = wpilib.drive.DifferentialDrive.curvatureDriveIK(forward, turn, True)

        self._left_volts_out.output = speeds.left * 12.0
        self._right_volts_out.output = speeds.right * 12.0

        self._left_leader.set_control(self._left_volts_out)
        self._right_leader.set_control(self._right_volts_out)

    def drive_volts(self, left: float, right: float) -> None:
        self._left_volts_out.output = left
        self._right_volts_out.output = right

        self._left_leader.set_control(self._left_volts_out)
        self._right_leader.set_control(self._right_volts_out)

    def __deadband(self, input: float, abs_min: float) -> float:
        """ """
        if abs_min < 0:
            abs_min *= -1

        if input < 0 and input > abs_min * -1:
            input = 0

        if input > 0 and input < abs_min:
            input = 0

        return input


    def get_Apriltag_status(self) -> bool:
        return self.camera_has_target.get()

    def get_Apriltag_yaw(self) -> float:
        return self.yaw_angle_to_target.get()

    def periodic(self) -> None:

        # print (self.rangefinder1.getAverageVoltage())
        
        wpilib.SmartDashboard.putNumber(
            "ShortRangeFinder", self.rangefinder1.getAverageVoltage()
        )

        wpilib.SmartDashboard.putBoolean(
            "PhotonVision: AprilTag in sight:", self.camera_has_target.get()
        )
        wpilib.SmartDashboard.putNumber(
            "Yaw Angle to AprilTag", self.yaw_angle_to_target.get()
        )

        # if self.camera_has_target.get():
        #     print ("TargetPreset", self.yaw_angle_to_target.get())
        # else:
        #     print("AprilTag Not Present")

        wpilib.SmartDashboard.putNumber(
            "LeftEncoder", self._left_leader.get_position().value
        )
        wpilib.SmartDashboard.putNumber(
            "RightEncoder", self._right_leader.get_position().value
        )

    def configure_motion_magic(self, distance_in_inches: float) -> None:
        """
        Method to configure the motors using a MotionMagic profile.

        :param: distance_in_inches  Distance in inches to travel.
        """
        # The TalonFX configuration already sets up the SensorToMechanism ratio when
        # it accounts for the position feedback.  So, when the talon.get_position()
        # method is called, it returns the roations of the wheel's output shaft, not
        # the input shaft of the gearbox.  So, if we were to use a setpoint of 1 (1 rotation)
        # in the MotionMagic profile, it would try to turn the wheels 1 rotation, not
        # the motor.

        # Convert the distance in inches, to wheel rotations
        #                          distance_in_inches
        # wheel_rotations =   --------------------------
        #                        Pi * Wheel Diameter
        distance_in_rotations = distance_in_inches / (
            math.pi * constants.DT_WHEEL_DIAMETER
        )
        curr_right = self._right_leader.get_position().value_as_double

        self._mm_out.with_position(curr_right + distance_in_rotations).with_slot(0)

    def drive_motion_magic(self) -> None:
        self._left_leader.set_control(Follower(self._right_leader.device_id, False))
        self._right_leader.set_control(self._mm_out)

    def at_mm_setpoint(self) -> bool:
        curr_right = self._right_leader.get_position().value

        return abs(self._mm_out.position - curr_right) < self._mm_tolerance

    def mm_drive_distance(self) -> Command:
        return (
            cmd.run(lambda: self.drive_motion_magic(), self)
            .until(lambda: self.at_mm_setpoint())
            .withName("DriveMM")
        )

    def mm_drive_config(self, distance_in_inches: float) -> Command:
        return cmd.runOnce(lambda: self.configure_motion_magic(distance_in_inches))

    def configure_turn_pid(self, desired_angle: float) -> Command:
        return cmd.runOnce(lambda: self.__config_turn_command(desired_angle))

    def turn_with_pid(self) -> Command:
        return (
            cmd.run(lambda: self.__turn_with_pid(), self)
            .until(lambda: self.__at_turn_setpoint())
            .withName("TurnWithPID")
        )

    def __config_turn_command(self, desired_angle: float) -> None:
        self._turn_setpoint = desired_angle + self._gyro.getYaw()
        self._turn_pid_controller.setSetpoint(self._turn_setpoint)
        self._turn_pid_controller.setTolerance(self._turn_tolerance)
        wpilib.SmartDashboard.putNumber("Turn Setpoint", self._turn_setpoint)

    def __turn_with_pid(self) -> None:
        curr_angle = self._gyro.getYaw()
        wpilib.SmartDashboard.putNumber("Yaw", curr_angle)

        pidoutput = self._turn_pid_controller.calculate(curr_angle)

        # Promote the value to at least the KF
        if (pidoutput < 0) and (pidoutput > -self._turn_kF):
            pidoutput = -self._turn_kF
        elif (pidoutput > 0) and (pidoutput < self._turn_kF):
            pidoutput = self._turn_kF

        wpilib.SmartDashboard.putNumber("PID Out", pidoutput)

        if RobotBase.isSimulation():
            self.drive_teleop(pidoutput, 0)
        else:
            self.drive_teleop(0, pidoutput)

    def __at_turn_setpoint(self) -> bool:
        curr_angle = self._gyro.getYaw()

        wpilib.SmartDashboard.putBoolean(
            "At Setpoint", self._turn_pid_controller.atSetpoint()
        )

        return abs(curr_angle - self._turn_setpoint) < self._turn_tolerance


class DriveMMInches(Command):
    def __init__(self, dt: DriveTrain, distance_in_inches: float) -> None:
        super().__init__()

        self._dt = dt
        self._desired_distance = distance_in_inches

        # Tell the scheduler this requires the drivetrain
        self.addRequirements(self._dt)

    def initialize(self):
        self._dt.configure_motion_magic(self._desired_distance)

    def execute(self):
        self._dt.drive_motion_magic()

    def isFinished(self) -> bool:
        return self._dt.at_mm_setpoint()

    def end(self, interrupted: bool):
        self._dt.drive_volts(0, 0)
