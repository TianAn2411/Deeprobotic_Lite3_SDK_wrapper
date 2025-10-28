"""
Example 1: Basic Control
=========================
This example demonstrates basic control of the Lite3 robot using the Python API.
"""
import pylite3
import os
import time
def main():
    print("=== Example 1: Basic Control ===\n")

    # Create controller in simulation mode
    robot = pylite3.Lite3Controller(use_sim=True)

    # Initialize (starts interfaces)
    robot.initialize()

    # Stand up
    print("Standing up...")
    robot.stand_up(duration=5.0, blocking=True)
    print("Standing complete!\n")

    # Wait a bit
    time.sleep(1.0)
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.abspath(os.path.join(script_dir, "../../"))
    # model_path = os.path.join(project_root, "policy/ppo/policy.onnx")
    # Vì bạn chạy script từ thư mục `python_package/examples`,
    # đường dẫn tương đối chính xác để đi lên thư mục gốc của dự án
    # và vào thư mục `policy` là `../../`.
    model_path = "../../policy/ppo/policy.onnx"

    # Tải mô hình ONNX giống như trong C
    print(f"Loading ONNX policy from: {model_path}")
    robot.load_onnx_policy(model_path)

    robot.run_async(pylite3.ControlMode.RL_CONTROL)

    print("Walking forward for 10 seconds...")
    robot.set_velocity(vx=0.5, vy=0.0, vyaw=0.0)
    time.sleep(7.0)

    print("Turning left for 5 seconds...")
    robot.set_velocity(vx=0.3, vy=0.0, vyaw=0.6)
    time.sleep(12.0)

    print("Turning right for 5 seconds...")
    robot.set_velocity(vx=0.3, vy=0.0, vyaw=-0.6)
    time.sleep(12.0)
   
    print("Walking forward for 10 seconds...")
    robot.set_velocity(vx=0.5, vy=0.0, vyaw=0.0)
    time.sleep(15.0)
    
    # Stop
    print("Stopping...")
    robot.set_velocity(vx=0.0, vy=0.0, vyaw=0.0)
    time.sleep(2.0)

    robot.stop()

    # Print performance stats
    print("\n" + robot.get_performance_stats())

    print("\nExample complete!")

if __name__ == "__main__":
    main()
