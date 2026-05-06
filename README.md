# 📱 Second-Hand Mobile Price Analyzer

## 📌 Project Overview
This project aims to build an intelligent system that analyzes second-hand mobile listings in Egypt (e.g., OLX) and determines whether the price is:

- ✅ Fair
- 🔥 Good Deal (Underpriced)
- ❌ Overpriced

The system relies on:
- 📷 Mobile images
- 📝 Seller descriptions
- 💰 Listed prices

---

## 🎯 Objectives
- Predict the **fair price** of a used mobile phone
- Classify listings into pricing categories
- Compare performance of multiple deep learning models
- Build a real-world multimodal AI system

---

## 🕸️ Data Collection
We use **web scraping** to collect data from online marketplaces.

### Collected Data:
- Mobile images
- Listing descriptions
- Prices

### Steps:
1. Scrape data from listing websites
2. Clean and preprocess data
3. Store in structured format (CSV / JSON)

---

## 🧠 Models Used

### 🖼️ Computer Vision Models
- **CNN (Convolutional Neural Network)**  
  - Built from scratch or using transfer learning  
  - Predicts phone condition or price from images  

- **Vision Transformer (ViT)**  
  - Pre-trained model fine-tuned on our dataset  
  - Compared against CNN performance  

---

### 📝 NLP Models
- **LSTM (Long Short-Term Memory)**  
  - Processes listing descriptions  
  - Handles Arabic, slang, and Franco text  

- **GRU (Gated Recurrent Unit)**  
  - Lightweight alternative to LSTM  
  - Used for comparison  

---

### 🔗 Multimodal Model
- Combines:
  - Image features (CNN / ViT)
  - Text features (LSTM / GRU)
- Uses Fully Connected layers to:
  - Predict price
  - Classify deal quality

---

## 🏷️ Labeling Strategy
Listings are classified into:

- 🔥 **Good Deal** → Price significantly lower than expected  
- ✅ **Fair** → Price within normal range  
- ❌ **Overpriced** → Price higher than expected  

---

## ⚙️ System Components

### 1. Data Pipeline
- Web scraping
- Data cleaning
- Data labeling

### 2. Model Training
- Image models (CNN, ViT)
- Text models (LSTM, GRU)
- Multimodal model

### 3. API
- Built using **Flask / FastAPI**
- Accepts:
  - Image
  - Description
  - Price
- Returns:
  - Predicted fair price
  - Deal classification

### 4. Demo
- Simple UI using:
  - Streamlit or Notebook

---

## 👥 Team Distribution

### 👤 Member 1
- CNN Model
- Web Scraping
- Data collection & cleaning

### 👤 Member 2
- Vision Transformer (ViT)
- Image augmentation
- Model evaluation

### 👤 Member 3
- LSTM Model
- NLP pipeline (Arabic processing)

### 👤 Member 4
- GRU Model
- Data labeling
- Data preparation support

### 👤 Member 5
- Multimodal Model
- API development
- Demo preparation

---

## 📊 Evaluation Metrics

### For Regression (Price Prediction):
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)

### For Classification:
- Accuracy
- Precision / Recall / F1-score

---

## 🚀 Future Improvements
- Use larger dataset
- Deploy as a web app
- Add real-time scraping
- Improve Arabic NLP handling

---

## 🛠️ Tech Stack
- Python
- TensorFlow / PyTorch
- OpenCV
- Transformers (Hugging Face)
- BeautifulSoup / Scrapy
- Flask / FastAPI
- Streamlit

---

## 📌 How to Run

```bash
# Clone repo
git clone https://github.com/your-repo-name.git

# Install dependencies
pip install -r requirements.txt

# Run training
python train.py

# Run API
python app.py
