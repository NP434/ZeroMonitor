# ZeroMonitor  
**Agent-less Hardware Monitoring System**  
*ERAU Capstone Project*

---

## Overview  
ZeroMonitor is a lightweight, agent-less hardware monitoring system designed to collect and display system metrics without requiring software installation on target machines.  

The project focuses on delivering a **scalable, low-overhead solution** for monitoring system health across multiple devices in real time.

Unlike traditional monitoring tools that rely on installed agents, ZeroMonitor uses **network-based data collection**, reducing system impact and simplifying deployment.

---

## Features  
- 🛰️ Agent-less monitoring (no installation required on client machines)  
- ⚡ Real-time system metrics collection  
- 🪶 Lightweight and low resource usage  
- 🌐 Cross-platform compatibility  
- 📈 Scalable architecture for multiple devices  
- 🎨 Clean and intuitive data visualization interface  

---

## Architecture  

ZeroMonitor follows a **client-server model**:

### 🔹 Target Systems  
- No installed agents  
- Expose hardware/system data through accessible interfaces  

### 🔹 Backend
- Collects and processes system data  
- Normalizes and stores metrics  

### 🔹 Frontend Interface  
- Displays real-time hardware data  
- Provides a user-friendly dashboard  

---

## Prerequisites  
- Python 3  

---

## Example Metrics Collected  
- CPU usage  
- Memory usage  
- Disk utilization  
- Network activity  

---

## Project Goals  
- Eliminate the need for intrusive monitoring agents  
- Provide a simple deployment model  
- Enable real-time visibility into system performance  
- Build a scalable monitoring solution for enterprise environments  

---

## Contributors  




---

![Coverage](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO/branch/main/graph/badge.svg)
[![Run Pytest](https://github.com/NP434/ZeroMonitor/actions/workflows/tests.yml/badge.svg)](https://github.com/NP434/ZeroMonitor/actions/workflows/tests.yml)
