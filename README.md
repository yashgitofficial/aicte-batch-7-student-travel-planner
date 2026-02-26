🎒 Student AI Travel Planner
A generative AI-powered travel planning dashboard built for students to create personalized, budget-friendly itineraries. This application leverages the Google Gemini API to generate structured travel plans based on user preferences, budget constraints, and duration. It features an interactive UI with downloadable itineraries, personalized note-taking, and dynamic map styling.

🚀 Live Demo
Click here to view the live deployed application

(Note: The live deployment uses Streamlit Secrets for secure API key management).

✨ Key Features
AI-Powered Itineraries: Utilizes gemini-2.5-flash to generate strict, JSON-formatted travel plans tailored to specific interests (e.g., Street Food, Free Activities).
Smart Budget Tracker: Automatically compares the user's strict budget against the AI's estimated activity costs, providing visual metrics and warnings.
Multi-Theme Interactive Mapping: Integrates geopy and folium to plot activities dynamically. Users can seamlessly toggle between Standard, Dark Mode, and Terrain map styles without losing data.
Session State Management: Built with advanced Streamlit session state caching to ensure AI-generated data is preserved during UI interactions and map theme changes.
Downloadable Itineraries: Users can export their complete, formatted travel plan as a text file for offline use.
Travel Notebook (Multi-Tab UI): Features a dedicated workspace tab for users to jot down flight numbers, packing lists, and custom notes during their session.
Dynamic Fallback Geocoding: Implements a multi-tier search system to accurately place map pins even if the AI generates vague location descriptions.
🛠️ Technology Stack
Frontend/Framework: Streamlit
AI Engine: Google Generative AI SDK (google-genai)
Mapping & Geocoding: Folium, Streamlit-Folium, Geopy (Nominatim)
Data Processing: Pandas, JSON, Regular Expressions (RegEx)
Deployment: Streamlit Community Cloud
💻 How to Run Locally (For Evaluators)
If you wish to run this application on your local machine rather than using the live demo, follow these steps:

Clone the repository:
git clone [https://github.com/yashgitofficial/aicte-batch-7-student-travel-planner.git](https://github.com/yashgitofficial/aicte-batch-7-student-travel-planner.git)
cd aicte-batch-7-student-travel-planner
