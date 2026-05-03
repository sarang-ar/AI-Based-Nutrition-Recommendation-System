# 🧠 AI-Based Nutrition Recommendation System

An intelligent full-stack web application that generates **personalized diet plans** based on user health data and preferences using **AI techniques and nutritional analysis**.

---

## 🚀 Project Overview

This project recommends meals by analyzing user inputs such as:

* Age, weight, height
* Activity level
* Fitness goals (weight loss, maintenance, gain)
* Dietary preferences

The system calculates:

* **BMI (Body Mass Index)**
* **BMR (Basal Metabolic Rate)**
* **TDEE (Total Daily Energy Expenditure)**

Then it uses a **content-based recommendation system (cosine similarity)** to suggest meals from a large food dataset.

---

## ✨ Features

* 🥗 Personalized meal plan generation
* 📊 Nutritional analysis (calories, protein, carbs, fats)
* ⚙️ Custom diet filtering (veg/non-veg, ingredients)
* 🤖 AI-based recommendation engine
* 🌐 Full-stack architecture (Frontend + Backend)
* 📦 Dockerized deployment
* 📈 Scalable and efficient for large datasets

---

## 🏗️ Tech Stack

### 🔹 Frontend

* React (TypeScript)
* Tailwind CSS (optional if used)

### 🔹 Backend

* FastAPI (Python)
* REST API architecture

### 🔹 AI / Data Processing

* Pandas, NumPy
* Cosine Similarity (content-based filtering)
* Nutrition dataset (Food.com / USDA)

### 🔹 DevOps & Tools

* Docker & Docker Compose
* Git & GitHub

---

## 🧠 How It Works

1. User inputs personal health data
2. Backend calculates:

   * BMI
   * BMR
   * TDEE
3. Nutritional requirements are determined
4. Food dataset is converted into feature vectors
5. Cosine similarity is used to find best matches
6. System returns optimized meal plan

---

## 📂 Project Structure

```
nutrimind/
│
├── FastAPI_Backend/        # Backend API
│   ├── main.py
│   ├── requirements.txt
│
├── react_frontend/         # Frontend UI
│   ├── src/
│   ├── package.json
│
├── docker-compose.yml      # Multi-container setup
├── food-recommendation-system.ipynb
├── README.md
```

---

## ⚙️ Installation & Setup

### 🔧 Prerequisites

* Python 3.8+
* Node.js
* Docker (optional)

---

### ▶️ Run Backend

```bash
cd FastAPI_Backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### ▶️ Run Frontend

```bash
cd react_frontend
npm install
npm start
```

---

### 🐳 Run with Docker

```bash
docker-compose up --build
```

---

## 📊 Dataset

Due to size limitations, datasets are not included in this repository.

👉 You can download from:

* USDA FoodData Central
* Food.com dataset

After downloading, place them in:

```
Data/
FoodData/
```

---

## 📈 Example Output

* Daily calorie target
* Recommended meals
* Nutritional breakdown
* Alternative food suggestions

---

## 🚧 Future Improvements

* 🔥 Deep learning-based recommendations
* 📱 Mobile app version
* 🧬 Health condition-based diet (diabetes, PCOS, etc.)
* 💬 Chat-based AI nutrition assistant
* 📊 Dashboard with analytics

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork the repo and submit a pull request.

---

## 📜 License

This project is for educational purposes.

---

## 👨‍💻 Author

**Sarang AR**

* GitHub: https://github.com/sarang-ar

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!

---
