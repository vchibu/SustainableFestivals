# Sustainable Festivals – Transport Simulation Framework

This project models and analyzes the transportation impact of festival attendees, with the goal of improving the environmental sustainability of large-scale events. Developed as part of the ISBEP graduation project at Eindhoven University of Technology, the simulation framework evaluates how different transportation strategies—based on cost, time, emissions, complexity, or realistic behavior—affect mobility outcomes for a 20,000-person crowd traveling to and from the Lakedance Festival. The simulation integrates real-world OpenStreetMap and GTFS data through a self-hosted OpenTripPlanner (OTP) server and includes modules for carbon footprint estimation, behavioral logic, and multimodal transport routing.

The framework is divided into two main components. The **First Order Simulation** models individual attendee trips using five different decision strategies, allowing for detailed comparisons across emissions, time, cost, and convenience. The **Second Order Simulation** builds on these results by requerying the realistic scenario and analyzing road congestion, infrastructure usage, and potential externalities for non-attendees. The system is designed with modular Python classes, enabling extensibility to other festivals, cities, or transport interventions.

## 🚀 How to Run the Simulation

1. **Clone the repository.**

2. **Install dependencies using:**
   bash
   pip install -r requirements.txt

3. **Start the OTP server:**
    cd SustainableFestivals/OTP-Server
    java -Xmx4G -jar otp-shaded-2.7.0.jar --load ./Graph --serve
(You can increase the -Xmx4G flag depending on available RAM.)


4. **Run the First Order Simulation:**
    Open FirstOrderSimulation/Code/CallingCode/main.py and configure:
        - Which scenarios to run (carbon, cost, time, leg, realistic)
        - Whether to use precomputed data or rerun different parts of the simulation
    Then execute FirstOrderSimulation/main.py

5. **Run the Second Order Simulation:**
    Make sure that results from the realistic scenario already exist.
    Then execute: SecondOrderSimulation/main.py