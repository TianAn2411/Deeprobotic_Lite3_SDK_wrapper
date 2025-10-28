/**
 * @file simple_example.cpp
 * @brief Simple example of using Lite3Controller
 * @author HaiHa
 * @version 1.0
 * @date 2025-10-23
 */

#include "lite3_controller.hpp"
#include <iostream>
#include <chrono>
#include <thread>

using namespace lite3_api;

int main() {
    std::cout << "=== Lite3 Simple Example ===" << std::endl;

    // Create controller in simulation mode
    Lite3Controller robot(true);

    // Initialize
    robot.initialize();

    // Stand up
    std::cout << "Standing up..." << std::endl;
    robot.standUp(2.0f, true);

    // Wait a bit
    std::this_thread::sleep_for(std::chrono::seconds(5));

    //Phải tải chính sách onnx về thì nó mới di chueyẻn
    std::string model_path = "../policy/ppo/policy.onnx";
    robot.loadONNXPolicy(model_path);

    //chế độ chạy phải là RL_COntrol
    robot.runAsync(ControlMode::RL_CONTROL);

    // Đặt vận tốc mục tiêu
    std::cout << "Walking forward..." << std::endl;
    robot.setVelocity(0.5f, 0.0f, 0.0f); // Đặt vận tốc tiến hợp lý (giá trị từ -1.0 đến 1.0)
    std::this_thread::sleep_for(std::chrono::seconds(7));

    std::cout << "Turning left..." << std::endl;
    robot.setVelocity(0.5f, 0.0f, 0.6f);
    std::this_thread::sleep_for(std::chrono::seconds(12));

    std::cout << "Turning right..." << std::endl;
    robot.setVelocity(0.5f, 0.0f, -0.6f);
    std::this_thread::sleep_for(std::chrono::seconds(12));

    std::cout << "Walking forward..." << std::endl;
    robot.setVelocity(0.5f, 0.0f, 0.0f); // Đặt vận tốc tiến hợp lý (giá trị từ -1.0 đến 1.0)
    std::this_thread::sleep_for(std::chrono::seconds(15));
    // Stop
    robot.stop();

    // Print performance stats
    std::cout << robot.getPerformanceStats() << std::endl;

    std::cout << "Example complete!" << std::endl;

    return 0;
}
