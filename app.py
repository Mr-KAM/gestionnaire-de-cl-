########################################################
#          IMPORTATOON DES PACKAGES                    #
########################################################

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
import pandas as pd
import re
import streamlit_shadcn_ui as ui
from st_aggrid import AgGrid
from itables.streamlit import interactive_table
# --------------------- Configuration de SQLAlchemy ---------------------

Base = declarative_base()
engine = create_engine('sqlite:///keys.db', echo=True)
Session = sessionmaker(bind=engine)

# --------------------- Modèles ---------------------
class Emprunteur(Base):
    __tablename__ = 'emprunteurs'
    id = Column(Integer, primary_key=True)
    matricule = Column(String(50), unique=True, nullable=False)
    nom = Column(String(100), nullable=False)
    prenoms = Column(String(100), nullable=False)
    telephone = Column(String(20))
    email = Column(String(100))
    date_creation = Column(DateTime, default=datetime.now)
    emprunts = relationship("Emprunt", back_populates="emprunteur")

class Salle(Base):
    __tablename__ = 'salles'
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    capacite = Column(Integer)
    equipements = Column(Text)
    date_creation = Column(DateTime, default=datetime.now)
    cles = relationship("Cle", back_populates="salle")

class Cle(Base):
    __tablename__ = 'cles'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    salle_id = Column(Integer, ForeignKey('salles.id'))
    est_disponible = Column(Boolean, default=True)
    salle = relationship("Salle", back_populates="cles")
    emprunts = relationship("Emprunt", back_populates="cle")

class Emprunt(Base):
    __tablename__ = 'emprunts'
    id = Column(Integer, primary_key=True)
    cle_id = Column(Integer, ForeignKey('cles.id'))
    emprunteur_id = Column(Integer, ForeignKey('emprunteurs.id'))
    activite = Column(Text)
    date_emprunt = Column(DateTime, nullable=False, default=datetime.now)
    date_restitution_prevue = Column(DateTime, nullable=False)
    date_restitution = Column(DateTime, nullable=True)
    cle = relationship("Cle", back_populates="emprunts")
    emprunteur = relationship("Emprunteur", back_populates="emprunts")

# --------------------- Création de la Base de donnée ---------------------
Base.metadata.create_all(engine)


########################################################
#                     UI DE L'APPLICATION              #
########################################################


# --------------------- Page dashboard ---------------------
def page_dashboard():
    """
    Tableau de bord : Affiche des statistiques globales et un tableau/graphique sur la disponibilité des salles.
    """
    st.title("📊 Tableau de bord")

    session = Session()

    # Quelques statistiques globales
    total_salles = session.query(Salle).count()
    total_emprunteurs = session.query(Emprunteur).count()
    total_emprunts = session.query(Emprunt).count()
    total_cles = session.query(Cle).count()
    cles_occupees = session.query(Cle).filter(Cle.est_disponible == False).count()

    # Affichage sous forme de métriques

    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Nombre de salles", content=total_salles, description="+20.1% from last month", key="card1")
    with cols[1]:
        ui.metric_card(title="Nombre d'emprunteurs", content=total_emprunteurs, description="+20.1% from last month", key="card2")
    with cols[2]:
        ui.metric_card(title="Nombre d'emprunts", content=total_emprunts, description="+20.1% from last month", key="card3")
    st.markdown("---")
    st.subheader("Disponibilité des salles")

    # Disponibilité : On considère une salle occupée si au moins une clé n'est pas disponible
    salles_data = session.query(Salle).all()
    stat_data = []
    for salle in salles_data:
        if not salle.cles:
            # Pas de clé => on considère la salle comme Indéterminée
            stat_data.append({
                "Salle": salle.nom,
                "Statut": "Pas de clé"
            })
        else:
            # Si une clé est indisponible => Occupée, sinon Disponible
            is_occupied = any(not c.est_disponible for c in salle.cles)
            stat_data.append({
                "Salle": salle.nom,
                "Statut": "Occupée" if is_occupied else "Disponible"
            })

    df_stat = pd.DataFrame(stat_data)

        # Diagramme de barres : distribution de la colonne "Statut"
    stats_count = df_stat["Statut"].value_counts().reset_index()
    stats_count.columns = ["Statut", "Nombre de salles"]
    st.bar_chart(data=stats_count, x="Statut", y="Nombre de salles")
    # with ui.card(key="table_card"):
        # AgGrid(df_stat)
    interactive_table(df_stat,buttons=['copyHtml5', 'csvHtml5', 'excelHtml5', 'colvis'])
        # ui.table(data=df_stat, maxHeight=100)



    session.close()



# --------------------- Page liste des Salles ---------------------
def page_liste_salles():
    st.title("Liste des Salles")

    session = Session()
    salles = session.query(Salle).all()
    if salles:
        data = [
            {
                "Nom": s.nom,
                "Capacité": s.capacite,
                "Équipements": s.equipements,
                "Description": s.description
            } for s in salles
        ]
        # st.dataframe(pd.DataFrame(data))
        ui.table(data=pd.DataFrame(data), maxHeight=300)
    else:
        st.info("Aucune salle enregistrée.")
    session.close()

# --------------------- Page ajout de salle ---------------------
def page_ajouter_salle():
    st.title("Ajouter une Salle")
    with st.form("ajout_salle"):
        nom = st.text_input("Nom de la salle")
        capacite = st.number_input("Capacité", min_value=1)
        equipements = st.text_area("Équipements")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            session = Session()
            try:
                # Création de la salle
                new_salle = Salle(nom=nom, capacite=capacite, equipements=equipements, description=description)
                session.add(new_salle)
                session.flush()  # pour obtenir l'ID avant de commit
                # Création automatique d'une clé pour la salle
                new_key = Cle(code=f"KEY-{new_salle.id:03d}", salle_id=new_salle.id, est_disponible=True)
                session.add(new_key)
                session.commit()
                st.success(f"Salle ajoutée avec succès! Clé créée: {new_key.code}")
            except Exception as ex:
                session.rollback()
                st.error(f"Erreur lors de l'ajout: {str(ex)}")
            finally:
                session.close()

# ------------------ Page Importation de salles via CSV ------------------
def page_import_salles_csv():
    st.title("Importer des Salles depuis un CSV")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        if st.button("Importer"):
            session = Session()
            lignes_importees = 0
            try:
                for idx, row in df.iterrows():
                    nom = str(row.get("nom", "")).strip()
                    capacite = int(row.get("capacite", 0))
                    equipements = str(row.get("equipements", ""))
                    description = str(row.get("description", ""))

                    if not nom:
                        st.warning(f"Ligne {idx}: Le nom de la salle est vide, ignoré.")
                        continue

                    # Vérifier l'existence
                    existing = session.query(Salle).filter_by(nom=nom).first()
                    if existing:
                        st.info(f"La salle '{nom}' existe déjà, ignoré.")
                        continue

                    # Créer la salle
                    new_salle = Salle(
                        nom=nom,
                        capacite=capacite,
                        equipements=equipements,
                        description=description
                    )
                    session.add(new_salle)
                    session.flush()

                    # Créer la clé associée
                    new_key = Cle(code=f"KEY-{new_salle.id:03d}", salle_id=new_salle.id, est_disponible=True)
                    session.add(new_key)

                    lignes_importees += 1

                session.commit()
                st.success(f"Importation terminée. {lignes_importees} salles créées.")
            except Exception as ex:
                session.rollback()
                st.error(f"Erreur lors de l'import: {str(ex)}")
            finally:
                session.close()

# --------------------- Page modifier salle ---------------------

def page_modifier_salle():
    st.title("Modifier une Salle")
    session = Session()
    salles = session.query(Salle).all()
    if not salles:
        st.warning("Aucune salle à modifier.")
        session.close()
        return

    noms_salles = {s.nom: s for s in salles}
    selected_salle_modifier = st.selectbox("Sélectionner une salle", list(noms_salles.keys()), key="select_salle_modifier")
    salle = noms_salles[selected_salle_modifier]

    nom = st.text_input("Nom", salle.nom)
    capacite = st.number_input("Capacité", min_value=0, value=salle.capacite)
    equipements = st.text_area("Équipements", salle.equipements if salle.equipements else "")
    description = st.text_area("Description", salle.description if salle.description else "")

    if st.button("Modifier"):
        try:
            salle.nom = nom
            salle.capacite = capacite
            salle.equipements = equipements
            salle.description = description
            session.commit()
            st.success("Salle mise à jour avec succès!")
        except Exception as ex:
            session.rollback()
            st.error(f"Erreur lors de la mise à jour: {str(ex)}")
    session.close()

# --------------------- Page détail de salle ---------------------

def page_detail_salle():
    st.title("Détails d'une Salle")
    session = Session()
    salles = session.query(Salle).all()
    if not salles:
        st.warning("Aucune salle disponible.")
        session.close()
        return

    noms_salles = {s.nom: s for s in salles}
    selected_salle_detail = st.selectbox("Sélectionner une salle", list(noms_salles.keys()), key="select_salle_detail")
    salle = noms_salles[selected_salle_detail]

    st.subheader(f"Informations : {salle.nom}")
    st.write(f"**Capacité :** {salle.capacite}")
    st.write(f"**Équipements :** {salle.equipements}")
    st.write(f"**Description :** {salle.description}")

    # Liste des clés de la salle
    st.subheader("Clés associées")
    if salle.cles:
        for c in salle.cles:
            st.write(f"- Code clé : {c.code} | Disponible : {c.est_disponible}")
    else:
        st.info("Aucune clé enregistrée pour cette salle.")

    session.close()

# --------------------- Page liste des Emprunteurs ---------------------
def page_liste_emprunteurs():
    st.title("Liste des Emprunteurs")
    session = Session()
    emprunteurs = session.query(Emprunteur).all()
    if emprunteurs:
        data = [
            {
                "Matricule": e.matricule,
                "Nom": e.nom,
                "Prénoms": e.prenoms,
                "Téléphone": e.telephone,
                "Email": e.email,
                "Date création": e.date_creation.strftime('%Y-%m-%d %H:%M') if e.date_creation else ""
            } for e in emprunteurs
        ]
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("Aucun emprunteur enregistré.")
    session.close()

def page_ajouter_emprunteur():
    st.title("Ajouter un Emprunteur")
    with st.form("ajout_emprunteur"):
        matricule = st.text_input("Matricule")
        nom = st.text_input("Nom")
        prenoms = st.text_input("Prénoms")
        telephone = st.text_input("Téléphone")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            session = Session()
            try:
                # Vérification d'unicité
                exist = session.query(Emprunteur).filter_by(matricule=matricule).first()
                if exist:
                    st.error("Un emprunteur avec ce matricule existe déjà!")
                else:
                    emprunteur = Emprunteur(
                        matricule=matricule,
                        nom=nom,
                        prenoms=prenoms,
                        telephone=telephone,
                        email=email
                    )
                    session.add(emprunteur)
                    session.commit()
                    st.success("Emprunteur ajouté avec succès!")
            except Exception as ex:
                session.rollback()
                st.error(f"Erreur lors de l'ajout: {str(ex)}")
            finally:
                session.close()

# ------------------ Page Importer emprunteurs via CSV ------------------
def page_import_emprunteurs_csv():
    st.title("Importer des Emprunteurs depuis un CSV")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        if st.button("Importer"):
            session = Session()
            lignes_importees = 0
            try:
                for idx, row in df.iterrows():
                    matricule = str(row.get("matricule", "")).strip()
                    nom = str(row.get("nom", "")).strip()
                    prenoms = str(row.get("prenoms", "")).strip()
                    telephone = str(row.get("telephone", ""))
                    email = str(row.get("email", ""))

                    if not matricule:
                        st.warning(f"Ligne {idx}: Matricule vide, ignoré.")
                        continue

                    # Vérification de l'existence
                    exist = session.query(Emprunteur).filter_by(matricule=matricule).first()
                    if exist:
                        st.info(f"L'emprunteur '{matricule}' existe déjà, ignoré.")
                        continue

                    new_emprunteur = Emprunteur(
                        matricule=matricule,
                        nom=nom,
                        prenoms=prenoms,
                        telephone=telephone,
                        email=email
                    )
                    session.add(new_emprunteur)
                    lignes_importees += 1

                session.commit()
                st.success(f"Importation terminée. {lignes_importees} emprunteurs créés.")
            except Exception as ex:
                session.rollback()
                st.error(f"Erreur lors de l'import: {str(ex)}")
            finally:
                session.close()

# --------------------- Page modifier emprunteur ---------------------
def page_modifier_emprunteur():
    st.title("Modifier un Emprunteur")
    session = Session()
    emprunteurs = session.query(Emprunteur).all()
    if not emprunteurs:
        st.warning("Aucun emprunteur à modifier.")
        session.close()
        return

    dic_emprunteurs = {f"{e.matricule} - {e.nom} {e.prenoms}": e for e in emprunteurs}
    selected_emprunteur_modifier = st.selectbox("Sélectionner un emprunteur", list(dic_emprunteurs.keys()), key="select_emprunteur_modifier")
    emp = dic_emprunteurs[selected_emprunteur_modifier]

    matricule = st.text_input("Matricule", emp.matricule)
    nom = st.text_input("Nom", emp.nom)
    prenoms = st.text_input("Prénoms", emp.prenoms)
    telephone = st.text_input("Téléphone", emp.telephone if emp.telephone else "")
    email = st.text_input("Email", emp.email if emp.email else "")

    if st.button("Modifier"):
        try:
            # On pourrait vérifier si le matricule a changé et est déjà pris
            exist_m = session.query(Emprunteur).filter_by(matricule=matricule).first()
            if exist_m and exist_m.id != emp.id:
                st.error("Ce matricule est déjà utilisé par un autre emprunteur!")
            else:
                emp.matricule = matricule
                emp.nom = nom
                emp.prenoms = prenoms
                emp.telephone = telephone
                emp.email = email
                session.commit()
                st.success("Emprunteur mis à jour avec succès!")
        except Exception as ex:
            session.rollback()
            st.error(f"Erreur lors de la mise à jour: {str(ex)}")
    session.close()


# --------------------- Page detail emprunteur ---------------------

def page_detail_emprunteur():
    st.title("Détails d'un Emprunteur")
    session = Session()
    emprunteurs = session.query(Emprunteur).all()
    if not emprunteurs:
        st.warning("Aucun emprunteur enregistré.")
        session.close()
        return

    dic_emprunteurs = {f"{e.matricule} - {e.nom} {e.prenoms}": e for e in emprunteurs}
    selected_emprunteur_detail = st.selectbox("Sélectionner un emprunteur", list(dic_emprunteurs.keys()), key="select_emprunteur_detail")
    emp = dic_emprunteurs[selected_emprunteur_detail]

    st.subheader("Informations générales")
    st.write(f"**Matricule :** {emp.matricule}")
    st.write(f"**Nom :** {emp.nom}")
    st.write(f"**Prénoms :** {emp.prenoms}")
    st.write(f"**Téléphone :** {emp.telephone}")
    st.write(f"**Email :** {emp.email}")
    st.write(f"**Date création :** {emp.date_creation.strftime('%Y-%m-%d %H:%M') if emp.date_creation else ''}")

    # Afficher la liste de ses emprunts
    st.subheader("Historique des Emprunts")
    emprunts = emp.emprunts
    if emprunts:
        for idx, e in enumerate(emprunts, start=1):
            st.markdown(f"**Emprunt {idx}:**")
            st.write(f"- Salle : {e.cle.salle.nom}")
            st.write(f"- Code Clé : {e.cle.code}")
            st.write(f"- Activité : {e.activite}")
            st.write(f"- Date d'emprunt : {e.date_emprunt.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"- Date de restitution prévue : {e.date_restitution_prevue.strftime('%Y-%m-%d')}")
            if e.date_restitution:
                st.write(f"- Restitué le : {e.date_restitution.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.write("- **Statut :** En cours")
            st.write("---")
    else:
        st.info("Aucun emprunt pour cet emprunteur.")

    session.close()

# --------------------- Page liste des Emprunts ---------------------
def page_liste_emprunts():
    st.title("Liste des Emprunts")
    session = Session()
    emprunts = session.query(Emprunt).all()
    if not emprunts:
        st.info("Aucun emprunt enregistré.")
        session.close()
        return

    data = []
    for e in emprunts:
        data.append({
            "Emprunteur": f"{e.emprunteur.nom} {e.emprunteur.prenoms}",
            "Matricule": e.emprunteur.matricule,
            "Salle": e.cle.salle.nom,
            "Code clé": e.cle.code,
            "Activité": e.activite,
            "Date Emprunt": e.date_emprunt.strftime('%Y-%m-%d %H:%M'),
            "Date Retour Prévue": e.date_restitution_prevue.strftime('%Y-%m-%d'),
            "Date Retour": e.date_restitution.strftime('%Y-%m-%d %H:%M') if e.date_restitution else "En cours"
        })

    st.dataframe(pd.DataFrame(data))
    session.close()

# --------------------- Page ajouter un emprunt ---------------------

def page_ajouter_emprunt():
    st.title("Ajouter un Emprunt")
    session = Session()

    # Récupération des clés disponibles
    cles_dispo = session.query(Cle).filter(Cle.est_disponible == True).all()
    emprunteurs = session.query(Emprunteur).all()

    if not cles_dispo:
        st.warning("Aucune clé disponible.")
        session.close()
        return

    if not emprunteurs:
        st.warning("Aucun emprunteur enregistré.")
        session.close()
        return

    dic_cles = {f"{c.code} - Salle {c.salle.nom}": c for c in cles_dispo}
    dic_emprunteurs = {f"{e.matricule} - {e.nom} {e.prenoms}": e for e in emprunteurs}

    with st.form("form_ajout_emprunt"):
        selected_cle = st.selectbox("Sélectionner la clé", list(dic_cles.keys()), key="select_cle")
        selected_emprunteur = st.selectbox("Sélectionner l'emprunteur", list(dic_emprunteurs.keys()), key="select_emprunteur")
        activite = st.text_area("Activité")
        date_retour_prevue = st.date_input("Date de restitution prévue", min_value=date.today())
        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            try:
                la_cle = dic_cles[selected_cle]
                emp = dic_emprunteurs[selected_emprunteur]
                nouvel_emprunt = Emprunt(
                    cle_id=la_cle.id,
                    emprunteur_id=emp.id,
                    activite=activite,
                    date_restitution_prevue=date_retour_prevue
                )
                la_cle.est_disponible = False
                session.add(nouvel_emprunt)
                session.commit()
                st.success("Emprunt enregistré avec succès!")
            except Exception as e:
                session.rollback()
                st.error(f"Erreur lors de l'enregistrement: {str(e)}")
    session.close()

# --------------------- Page detail emprunt ---------------------
def page_detail_emprunt():
    st.title("Détails d'un Emprunt")
    session = Session()
    emprunts = session.query(Emprunt).all()
    if not emprunts:
        st.warning("Aucun emprunt enregistré.")
        session.close()
        return

    dic_emprunts = {}
    for e in emprunts:
        nom_emp = f"{e.emprunteur.nom} {e.emprunteur.prenoms} ({e.emprunteur.matricule})"
        salle_nom = e.cle.salle.nom if e.cle.salle else "Salle inconnue"
        label = f"Emprunt #{e.id} - {nom_emp} - Salle: {salle_nom}"
        dic_emprunts[label] = e

    selected_emprunt_detail = st.selectbox("Sélectionner un emprunt", list(dic_emprunts.keys()), key="select_emprunt_detail")
    emprunt = dic_emprunts[selected_emprunt_detail]

    st.write(f"**Emprunteur :** {emprunt.emprunteur.nom} {emprunt.emprunteur.prenoms}")
    st.write(f"**Matricule :** {emprunt.emprunteur.matricule}")
    st.write(f"**Salle :** {emprunt.cle.salle.nom}")
    st.write(f"**Clé :** {emprunt.cle.code}")
    st.write(f"**Activité :** {emprunt.activite}")
    st.write(f"**Date d'emprunt :** {emprunt.date_emprunt.strftime('%Y-%m-%d %H:%M')}")
    st.write(f"**Date de restitution prévue :** {emprunt.date_restitution_prevue.strftime('%Y-%m-%d')}")
    if emprunt.date_restitution:
        st.write(f"**Restitué le :** {emprunt.date_restitution.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.write("**Statut :** En cours")

    # Bouton de restitution si pas encore restitué
    if not emprunt.date_restitution:
        if st.button("Restituer la clé"):
            try:
                emprunt.date_restitution = datetime.now()
                emprunt.cle.est_disponible = True
                session.commit()
                st.success("Clé restituée avec succès!")
                st.experimental_rerun()
            except Exception as ex:
                session.rollback()
                st.error(f"Erreur lors de la restitution: {str(ex)}")

    session.close()

# --------------------- Gestionnaire de salle ---------------------
def gestion_salle():
    pages_salle={
        "Liste des salles": page_liste_salles,
        "Ajouter une salle": page_ajouter_salle,
        "Importer des salles via (CSV)": page_import_salles_csv,
        "Modifier une salle": page_modifier_salle,
        "Détails de salle": page_detail_salle,
    }
    list_salle, ajout_salle, import_salles_csv, modifier_salle, detail_salle = st.tabs(
        ["🗝️Liste","➕Ajouter", " 📄Importer via (CSV)","✏️Modifier", "🔍Détails"]
        )
    with list_salle:
        page_liste_salles()
    with ajout_salle:
        page_ajouter_salle()
    with import_salles_csv:
        page_import_salles_csv()
    with modifier_salle:
        page_modifier_salle()
    with detail_salle:
        page_detail_salle()

def gestion_emprunteur():
    pages_emprunteur={
        "Liste des emprunteurs": page_liste_emprunteurs,
        "Ajouter un emprunteur": page_ajouter_emprunteur,
        "Importer des emprunteurs (CSV)": page_import_emprunteurs_csv,
        "Modifier un emprunteur": page_modifier_emprunteur,
        "Détails d'un emprunteur": page_detail_emprunteur,
    }
    list_emprunteur, ajout_emprunter, import_emprunters_csv, modifier_emprunter, detail_emprunter = st.tabs(
        ["🙎🏿Liste","➕Ajouter", " 📄Importer via (CSV)","✏️Modifier", "🔍Détails"]
        )
    with list_emprunteur:
        page_liste_emprunteurs()
    with ajout_emprunter:
        page_ajouter_emprunteur()
    with import_emprunters_csv:
        page_import_emprunteurs_csv()
    with modifier_emprunter:
        page_modifier_emprunteur()
    with detail_emprunter:
        page_detail_emprunteur()

def gestion_emprunt():
    pages_emprunt={
        "Liste des emprunts": page_liste_emprunts,
        "Ajouter un emprunt": page_ajouter_emprunt,
        "Détails d'un emprunt": page_detail_emprunt
    }
    list_emprunt, ajout_emprunt, import_emprunts_csv, modifier_emprunt, detail_emprunt = st.tabs(
        ["🙎🏿Liste","➕Ajouter", " 📄Importer via (CSV)","✏️Modifier", "🔍Détails"]
        )
    with list_emprunt:
        page_liste_emprunts()
    with ajout_emprunt:
        page_ajouter_emprunt()
    with import_emprunts_csv:
        "En cours de développement"
    with modifier_emprunt:
        "En cours de développement"
    with detail_emprunt:
        page_detail_emprunt()

########################################################
#                   FONCTION PRINCIPALE                #
########################################################
def main():
    st.set_page_config(page_title="Gestion des Salles et Emprunteurs de clé de l'ESA", layout="wide", menu_items=None, page_icon="🔑")
    st.sidebar.title("Navigation")
    pages = {
        "📊Tableau de bord": page_dashboard,
        "🏠Gerer les salles": gestion_salle,
        "🙎🏿Gerer les emprunteurs": gestion_emprunteur,
        "🗝️Gerer les emprunts de clés": gestion_emprunt,

    }
    page=ui.tabs(options=["📊Tableau de bord", "🏠Gerer les salles", "🗝️Gerer les emprunts de clés","🙎🏿Gerer les emprunteurs"], default_value="📊Tableau de bord", key="liste_pages")
    # choix = st.sidebar.radio("Sélectionner une page", list(pages.keys()))
    pages[page]()

if __name__ == "__main__":
    main()
