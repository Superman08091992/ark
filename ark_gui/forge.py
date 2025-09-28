import streamlit as st, requests

st.title("A.R.K. Modular AI System")

inp=st.text_area("Enter request")
if st.button("Submit"):
    try:
        r=requests.post("http://localhost:8000/process",json={"request":inp})
        st.write(r.json())
    except Exception as e: 
        st.error(str(e))
