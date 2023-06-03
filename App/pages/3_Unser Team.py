import streamlit as st

def about_page():
    st.title("About the Team")
    st.write("Unser wunderbares Projektteam!")
    team_members = [
        {
            "name": "Deniz Harimci",
            "position": "CTO",
            "image_url": "img/deniz.jpg",
            "details": "Mit Zuversicht sehe ich uns gemeinsam Großartiges erreichen, indem wir unsere technische Expertise und Innovationskraft einsetzen."
        },
        {
            "name": "Felix Humburg",
            "position": "CEO",
            "image_url": "img/felix.jpg",
            "details": "Als CEO bin ich zuversichtlich, dass wir gemeinsam großartige Ergebnisse erzielen werden."
        },
        {
            "name": "Jeff Mulavarikkal",
            "position": "CIO",
            "image_url": "img/jeff.jpg",
            "details": "Als Chief Officer for Innovation bin ich zuversichtlich, dass wir durch strategische Innovationsführung und die Förderung einer innovationsfreundlichen Kultur gemeinsam Großes erreichen werden."
        },
        {
            "name": "Loris Trotter",
            "position": "COO",
            "image_url": "img/loris.jpg",
            "details": "Ich bin zuversichtlich, dass wir durch effiziente Prozesse und eine optimierte Betriebsstruktur gemeinsam Großes erreichen können."
        },
        {
            "name": "Silvan Stöckli",
            "position": "CIO",
            "image_url": "img/silvan.jpg",
            "details": "Als CIO sehe ich uns in der gemeinsamen Nutzung unserer Informationstechnologie Großes erreichen."
        }
    ]
    
    for member in team_members:
        col1, col2 = st.columns(2)
        with col1:
            st.image(member["image_url"], width=200)
        with col2:
            st.subheader(member["name"])
            st.write(f"**Position:** {member['position']}")
            st.write(member["details"])
        st.write("---")
about_page()