import streamlit as st
import os
from config import load_config, save_config, NGINX_CONFIG_FILE
from repo import check_repo, clone_repo, pull_latest
from docker_ops import build_image, stop_container, run_container
from nginx import update_nginx_from_config

def render_variables(variables, key_prefix):
    updated = {}
    should_rerun = False
    
    if variables:
        cols = st.columns([3, 3, 1])
        cols[0].markdown("**Key**")
        cols[1].markdown("**Value**")
    
    for i, (k, v) in enumerate(variables.items()):
        cols = st.columns([3, 3, 1])
        new_k = cols[0].text_input("Key", k, key=f"{key_prefix}_k_{i}", label_visibility="collapsed")
        new_v = cols[1].text_input("Value", v, key=f"{key_prefix}_v_{i}", label_visibility="collapsed")
        
        if cols[2].button("Remove", key=f"{key_prefix}_del_{i}"):
            should_rerun = True
            continue
            
        if new_k:
            updated[new_k] = new_v

    if st.button("Add Variable", key=f"{key_prefix}_add"):
        counter = 1
        while f"NEW_VAR_{counter}" in updated:
            counter += 1
        updated[f"NEW_VAR_{counter}"] = "value"
        should_rerun = True
        
    return updated, should_rerun

def deploy_deployment(d):
    name = d["name"]
    repo = d["repo"]
    branch = d["branch"]
    port = d["port"]
    directory = f"/opt/apps/{name}"
    repo_url = f"https://github.com/{repo}.git"
    dockerfile_path = os.path.join(directory, d.get("dockerfile_path", "Dockerfile"))

    with st.spinner(f"Deploying {name}..."):
        if not os.path.exists(directory):
            clone_repo(directory, repo_url, branch)
        elif not check_repo(directory, repo_url):
            st.error(f"Directory {directory} exists but points to a different repo")
            return

        pull_latest(directory, branch)
        image_name = f"{repo.replace('/', '_')}:{branch}".lower()
        
        build_image(image_name, directory, dockerfile_path)
        stop_container(name)
        run_container(image_name, name, port, d.get("variables", {}))
        update_nginx_from_config(NGINX_CONFIG_FILE)
        st.success(f"Deployed {name} successfully!")

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

        with st.expander("Variables"):
            new_vars, rerun = render_variables(d.get("variables", {}), f"deploy_{idx}")
            d["variables"] = new_vars
            if rerun:
                save_config(cfg)
                st.rerun()


        col1, col2 = st.columns([1, 4])
        with col1:
             if st.button("Deploy", key=f"deploy-{idx}"):
                 deploy_deployment(d)
        with col2:
            if st.button("Delete Deployment", key=f"delete-{idx}"):
                deployments.pop(idx)
                save_config(cfg)
                st.rerun()

st.divider()
st.subheader("Add New Deployment")

if "new_deploy_vars" not in st.session_state:
    st.session_state.new_deploy_vars = {}

new_name = st.text_input("Name", key="new_name")
new_repo = st.text_input("Repo (org/repo)", key="new_repo")
new_branch = st.text_input("Branch", key="new_branch")
new_port = st.number_input("Port", min_value=1, max_value=65535, key="new_port")
new_route = st.text_input("Route", key="new_route")
new_server = st.text_input("Server", key="new_server")
new_dockerfile = st.text_input("Dockerfile Path", "Dockerfile", key="new_dockerfile")

with st.expander("Variables"):
    new_vars, rerun = render_variables(st.session_state.new_deploy_vars, "new_deploy")
    st.session_state.new_deploy_vars = new_vars
    if rerun:
        st.rerun()

if st.button("Add Deployment", key="add_new"):
    new = {
        "name": new_name,
        "repo": new_repo,
        "branch": new_branch,
        "port": new_port,
        "route": new_route,
        "server": new_server,
        "dockerfile_path": new_dockerfile,
        "variables": st.session_state.new_deploy_vars
    }
    deployments.append(new)
    save_config(cfg)
    st.success("Deployment added")
    
    for key in ["new_name", "new_repo", "new_branch", "new_port", "new_route", "new_server", "new_dockerfile", "new_deploy_vars"]:
        if key in st.session_state:
            del st.session_state[key]
            
    for key in list(st.session_state.keys()):
        if key.startswith("new_key_") or key.startswith("new_val_"):
            del st.session_state[key]
            
    st.rerun()

if st.button("Save All Changes"):
    save_config(cfg)
    st.success("Configuration saved")
