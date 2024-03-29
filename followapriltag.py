import commands2
import wpilib.drive

# Import the subsystem
from drivetrain import DriveTrain


class FollowAprilTag(commands2.CommandBase):
    def __init__(self, drivetrain: DriveTrain) -> None:
        super().__init__()

        self.drivetrain = drivetrain
        self.addRequirements(drivetrain)

    def initialize(self) -> None:
        print ("Started AUTO ")

    def execute(self) -> None:
        
        # Max yaw is about 20 degrees, 
        apriltag_present = self.drivetrain.get_Apriltag_status()

        # print (apriltag_present)

        turn = -self.drivetrain.get_Apriltag_yaw() * 0.02

        # print (turn) 

        maxspeed = 0.3

        if turn > maxspeed :
            turn = maxspeed
        if turn < -maxspeed :
            turn = -maxspeed
    
        wpilib.SmartDashboard.putNumber(
            "Autonomous turn", turn
        )

        # turn = 0.0
        forward = 0.15

        if apriltag_present:
            self.drivetrain.drive_teleop(forward, turn)    # (Turn , forward)  << This is not correct
        else:
            self.drivetrain.drive_teleop(0.0, 0.0)

 
    def end(self, interrupted: bool) -> None:
        self.drivetrain.drive_teleop(0.0, 0.0)    # Stop the robot
        

    def isFinished(self) -> bool:
        # This command should be triggered while a button is held
        # so we don't want it to finish on it's own.  So always return
        # false to keep the command running until the button is released.
        return False

