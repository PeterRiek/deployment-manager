import streamlit as st
from config import load_config, save_config

st.set_page_config(page_title="Deployment Manager", layout="wide")
st.title("Deployment Configuration")

cfg = load_config()
deployments = cfg.get("deployments", [])

st.subheader("Existing Deployments")

for idx, d in enumerate(deployments):
    with st.expander(f"{d['name']}"):
        d["name"] = st.text_input("Name", d["name"], key=f"name-{idx}")
        d["repo"] = st.text_input("Repo", d["repo"], key=f"repo-{idx}")
        d["branch"] = st.text_input("Branch", d["branch"], key=f"branch-{idx}")
        d["port"] = st.number_input("Port", d["port"], key=f"port-{idx}")
        d["route"] = st.text_input("Route", d["route"], key=f"route-{idx}")
        d["server"] = st.text_input("Server", d["server"], key=f"server-{idx}")
        d["dockerfile_path"] = st.text_input(
            "Dockerfile Path",
            d.get("dockerfile_path", "Dockerfile"),
            key=f"dockerfile-{idx}"
        )

        if st.button("Delete Deployment", key=f"delete-{idx}"):
            deployments.pop(idx)
            save_config(cfg)
            st.rerun()

st.divider()
st.subheader("Add New Deployment")

with st.form("new-deployment"):
    new = {
        "name": st.text_input("Name"),
        "repo": st.text_input("Repo (org/repo)"),
        "branch": st.text_input("Branch"),
        "port": st.number_input("Port", min_value=1, max_value=65535),
        "route": st.text_input("Route"),
        "server": st.text_input("Server"),
        "dockerfile_path": st.text_input("Dockerfile Path", "Dockerfile")
    }

    if st.form_submit_button("Add"):
        deployments.append(new)
        save_config(cfg)
        st.success("Deployment added")
        st.rerun()

if st.button("Save All Changes"):
    save_config(cfg)
    st.success("Configuration saved")
