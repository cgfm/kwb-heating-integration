#!/usr/bin/env bash
# KWB Development Helper Script
# Provides common development tasks for KWB Heating Integration

# Bash completion support: source this script to enable tab completion
# Usage: source ./dev-helper.sh --completion
# NOTE: This block must come before 'set -uo pipefail' so that sourcing
# this script for completion doesn't leak strict mode into the parent shell.
if [[ "${1:-}" == "--completion" ]]; then
    _dev_helper_completions() {
        local actions="start stop restart reset-kwb reset-full status logs logs-kwb open backup-config completion no-completion help"
        COMPREPLY=($(compgen -W "${actions}" -- "${COMP_WORDS[1]}"))
    }
    complete -F _dev_helper_completions ./dev-helper.sh
    complete -F _dev_helper_completions dev-helper.sh
    return 0 2>/dev/null || exit 0
fi

set -uo pipefail

CONTAINER_NAME="kwb-hass-test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo ""
    echo -e "${CYAN}🔧 KWB Development Helper${NC}"
    echo -e "${CYAN}=========================${NC}"
    echo ""
    echo -e "${YELLOW}Container:${NC}"
    echo -e "  ${GREEN}start${NC}          Start HA container"
    echo -e "  ${GREEN}stop${NC}           Stop HA container"
    echo -e "  ${GREEN}restart${NC}        Restart HA container"
    echo -e "  ${GREEN}status${NC}         Show container status"
    echo ""
    echo -e "${YELLOW}Reset:${NC}"
    echo -e "  ${GREEN}reset-kwb${NC}      Reset only KWB integration (keep HA running)"
    echo -e "  ${GREEN}reset-full${NC}     Full HA reset (stop container, delete config)"
    echo ""
    echo -e "${YELLOW}Logs & UI:${NC}"
    echo -e "  ${GREEN}logs${NC}           Show recent HA logs"
    echo -e "  ${GREEN}logs-kwb${NC}       Show KWB-specific logs"
    echo -e "  ${GREEN}open${NC}           Open HA web interface"
    echo ""
    echo -e "${YELLOW}Utilities:${NC}"
    echo -e "  ${GREEN}backup-config${NC}  Backup current HA config"
    echo -e "  ${GREEN}completion${NC}     Add tab completion to ~/.bashrc"
    echo -e "  ${GREEN}no-completion${NC}  Remove tab completion from ~/.bashrc"
    echo ""
    echo -e "${CYAN}Usage: ./dev-helper.sh <action>${NC}"
    echo -e "${CYAN}Example: ./dev-helper.sh reset-kwb${NC}"
}

reset_kwb() {
    echo -e "${YELLOW}🔄 Resetting KWB integration...${NC}"

    # Check if container is running
    if ! docker ps --filter "name=${CONTAINER_NAME}" --format "{{.Status}}" | grep -q .; then
        echo -e "${RED}❌ Container ${CONTAINER_NAME} is not running${NC}"
        return 1
    fi

    echo -e "${CYAN}1️⃣ Removing KWB integration config...${NC}"
    docker exec "${CONTAINER_NAME}" rm -f /config/.storage/core.config_entries
    docker exec "${CONTAINER_NAME}" rm -rf /config/.storage/kwb_heating*
    docker exec "${CONTAINER_NAME}" rm -f /config/configuration.yaml

    echo -e "${CYAN}2️⃣ Restarting Home Assistant...${NC}"
    docker restart "${CONTAINER_NAME}"

    echo -e "${GREEN}✅ KWB integration reset completed!${NC}"
    echo -e "${BLUE}💡 You can now reconfigure the integration in HA UI${NC}"
    echo -e "${CYAN}🌐 Opening HA web interface in 30 seconds...${NC}"
    sleep 30
    xdg-open "http://localhost:8123" 2>/dev/null || echo -e "${YELLOW}Open http://localhost:8123 in your browser${NC}"
}

reset_full() {
    echo -e "${YELLOW}🔄 Full HA reset...${NC}"

    echo -e "${CYAN}1️⃣ Stopping and removing container...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" down --remove-orphans 2>/dev/null || true
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    echo -e "${CYAN}2️⃣ Cleaning up config directory...${NC}"
    if [[ -d "${SCRIPT_DIR}/ha-config" ]]; then
        sudo rm -rf "${SCRIPT_DIR}/ha-config"
        echo -e "   ${GREEN}✅ Config directory removed${NC}"
    fi

    echo -e "${CYAN}3️⃣ Recreating container...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d

    echo -e "${CYAN}4️⃣ Waiting for Home Assistant to start...${NC}"
    local retries=0
    while [[ $retries -lt 60 ]]; do
        if curl -s --max-time 5 -o /dev/null "http://localhost:8123"; then
            break
        fi
        sleep 5
        retries=$((retries + 1))
        echo -e "   Waiting... (${retries}/60)"
    done

    if [[ $retries -ge 60 ]]; then
        echo -e "${RED}❌ Home Assistant did not start in time${NC}"
        return 1
    fi
    echo -e "   ${GREEN}✅ Home Assistant is up${NC}"

    echo -e "${GREEN}✅ Full HA reset completed!${NC}"
    echo -e "${BLUE}💡 Custom component is mounted via docker volume, ready to configure.${NC}"
}

start_container() {
    echo -e "${YELLOW}▶️ Starting HA container...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d
    echo -e "${GREEN}✅ Container started!${NC}"
}

restart_container() {
    echo -e "${YELLOW}🔄 Restarting HA container...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" restart
    echo -e "${GREEN}✅ Container restarted!${NC}"
}

stop_container() {
    echo -e "${YELLOW}🛑 Stopping HA container...${NC}"
    docker compose -f "${SCRIPT_DIR}/docker-compose.yml" down --remove-orphans 2>/dev/null || \
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    echo -e "${GREEN}✅ Container stopped!${NC}"
}

show_logs() {
    echo -e "${CYAN}📋 Recent HA logs...${NC}"
    docker logs "${CONTAINER_NAME}" --tail 50
}

show_kwb_logs() {
    echo -e "${CYAN}📋 KWB-specific logs...${NC}"
    docker logs "${CONTAINER_NAME}" 2>&1 | grep -i -C 1 "kwb" || echo -e "${YELLOW}No KWB logs found${NC}"
}

show_status() {
    echo -e "${CYAN}📊 Container status...${NC}"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    echo -e "${CYAN}📊 HA Health Check...${NC}"
    if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "http://localhost:8123" | grep -q "200"; then
        echo -e "${GREEN}✅ HA Web Interface is accessible${NC}"
    else
        echo -e "${RED}❌ HA Web Interface not accessible${NC}"
    fi
}

open_ha() {
    echo -e "${CYAN}🌐 Opening HA web interface...${NC}"
    xdg-open "http://localhost:8123" 2>/dev/null || echo -e "${YELLOW}Open http://localhost:8123 in your browser${NC}"
}

backup_config() {
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="${SCRIPT_DIR}/ha-config-backup-${timestamp}"

    if [[ -d "${SCRIPT_DIR}/ha-config" ]]; then
        echo -e "${CYAN}💾 Backing up HA config to ${backup_path}...${NC}"
        cp -r "${SCRIPT_DIR}/ha-config" "${backup_path}"
        echo -e "${GREEN}✅ Config backed up!${NC}"
    else
        echo -e "${RED}❌ No config directory found${NC}"
    fi
}

install_completion() {
    local bashrc="${HOME}/.bashrc"
    local completion_line="source \"${SCRIPT_DIR}/dev-helper.sh\" --completion"

    if grep -qF "dev-helper.sh\" --completion" "${bashrc}" 2>/dev/null; then
        echo -e "${YELLOW}Tab completion is already installed in ${bashrc}${NC}"
        return 0
    fi

    echo "" >> "${bashrc}"
    echo "# KWB dev-helper tab completion" >> "${bashrc}"
    echo "${completion_line}" >> "${bashrc}"
    echo -e "${GREEN}✅ Tab completion added to ${bashrc}${NC}"
    echo -e "${BLUE}💡 Open a new terminal or run 'source ~/.bashrc' to activate.${NC}"
}

remove_completion() {
    local bashrc="${HOME}/.bashrc"

    if ! grep -qF "dev-helper.sh\" --completion" "${bashrc}" 2>/dev/null; then
        echo -e "${YELLOW}Tab completion is not installed in ${bashrc}${NC}"
        return 0
    fi

    grep -vF "dev-helper.sh\" --completion" "${bashrc}" | grep -v "# KWB dev-helper tab completion" > "${bashrc}.tmp"
    mv "${bashrc}.tmp" "${bashrc}"
    echo -e "${GREEN}✅ Tab completion removed from ${bashrc}${NC}"
    echo -e "${BLUE}💡 Open a new terminal or run 'source ~/.bashrc' to apply.${NC}"
}

# Main script logic
action="${1:-help}"

case "${action,,}" in
    start)          start_container ;;
    stop)           stop_container ;;
    restart)        restart_container ;;
    reset-kwb)      reset_kwb ;;
    reset-full)     reset_full ;;
    logs)          show_logs ;;
    logs-kwb)      show_kwb_logs ;;
    status)        show_status ;;
    open)          open_ha ;;
    backup-config)  backup_config ;;
    completion)     install_completion ;;
    no-completion)  remove_completion ;;
    help)           show_help ;;
    *)
        echo -e "${RED}❌ Unknown action: ${action}${NC}"
        show_help
        exit 1
        ;;
esac
