# 🎒 Student AI Travel Planner

**A generative AI-powered travel planning dashboard built for students to create personalized, budget-friendly itineraries.** This application leverages the Google Gemini API to generate structured travel plans based on user preferences, budget constraints, and duration. It then automatically geocodes the recommended locations and plots them on an interactive map.

---

## 🚀 Live Demo
**[Click here to view the live deployed application](https://aicte-batch-7-student-travel-planner-gnsvybkzd7aacczauru5nr.streamlit.app/)**

*(Note: The live deployment uses Streamlit Secrets for secure API key management).*

---

## ✨ Key Features
* **AI-Powered Itineraries:** Utilizes `gemini-2.5-flash` to generate strict, JSON-formatted travel plans tailored to specific interests (e.g., Street Food, Free Activities).
* **Smart Budget Tracker:** Automatically compares the user's strict budget against the AI's estimated activity costs, providing visual metrics and warnings.
* **Interactive Mapping:** Integrates `geopy` and `folium` to convert AI-generated locations into real-world coordinates, plotted dynamically on an interactive map. Geocoding results are cached to optimize performance and prevent API rate limiting.
* **Dynamic Fallback Geocoding:** Implements a multi-tier search system to accurately place map pins even if the AI generates vague location descriptions.
* **Responsive UI:** Built with Streamlit, featuring day-by-day expandable timelines and clean dataframes powered by Pandas.

---

## 🛠️ Technology Stack
* **Frontend/Framework:** Streamlit
* **AI Engine:** Google Generative AI SDK (`google-genai`)
* **Mapping & Geocoding:** Folium, Streamlit-Folium, Geopy (Nominatim)
* **Data Processing:** Pandas, JSON, Regular Expressions (RegEx)
* **Deployment:** Streamlit Community Cloud (with GitHub Actions for continuous uptime)

---

## 💻 How to Run Locally (For Evaluators)

If you wish to run this application on your local machine rather than using the live demo, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/aicte-batch-7-student-travel-planner.git](https://github.com/yashgitofficial/aicte-batch-7-student-travel-planner.git)
   cd aicte-batch-7-student-travel-planner
