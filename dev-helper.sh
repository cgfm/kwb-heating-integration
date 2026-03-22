#!/usr/bin/env bash
# KWB Development Helper Script
# Provides common development tasks for KWB Heating Integration

set -uo pipefail

# Bash completion support: source this script to enable tab completion
# Usage: source ./dev-helper.sh --completion
if [[ "${1:-}" == "--completion" ]]; then
    _dev_helper_completions() {
        local actions="reset-kwb reset-full restart logs logs-kwb status open backup-config help"
        COMPREPLY=($(compgen -W "${actions}" -- "${COMP_WORDS[1]}"))
    }
    complete -F _dev_helper_completions ./dev-helper.sh
    complete -F _dev_helper_completions dev-helper.sh
    return 0 2>/dev/null || exit 0
fi

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
    echo -e "${YELLOW}Available actions:${NC}"
    echo -e "  ${GREEN}reset-kwb${NC}      Reset only KWB integration (keep HA running)"
    echo -e "  ${GREEN}reset-full${NC}     Full HA reset (stop container, delete config)"
    echo -e "  ${GREEN}restart${NC}        Restart HA container"
    echo -e "  ${GREEN}logs${NC}           Show recent HA logs"
    echo -e "  ${GREEN}logs-kwb${NC}       Show KWB-specific logs"
    echo -e "  ${GREEN}status${NC}         Show container status"
    echo -e "  ${GREEN}open${NC}           Open HA web interface"
    echo -e "  ${GREEN}backup-config${NC}  Backup current HA config"
    echo ""
    echo -e "${YELLOW}Tab completion:${NC}"
    echo -e "  source ./dev-helper.sh --completion"
    echo -e "  Add to ~/.bashrc to make it permanent."
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

    echo -e "${CYAN}5️⃣ Installing HACS...${NC}"
    docker exec -w /config "${CONTAINER_NAME}" bash -c \
        'wget -qO - https://get.hacs.xyz | bash -' && \
        echo -e "   ${GREEN}✅ HACS installed${NC}" || \
        echo -e "   ${RED}❌ HACS installation failed${NC}"

    echo -e "${CYAN}6️⃣ Restarting Home Assistant to load HACS...${NC}"
    docker restart "${CONTAINER_NAME}"

    echo -e "${GREEN}✅ Full HA reset completed!${NC}"
    echo -e "${BLUE}💡 HA is restarting with HACS, this may take a minute...${NC}"
}

restart_container() {
    echo -e "${YELLOW}🔄 Restarting HA container...${NC}"
    docker restart "${CONTAINER_NAME}"
    echo -e "${GREEN}✅ Container restarted!${NC}"
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

# Main script logic
action="${1:-help}"

case "${action,,}" in
    reset-kwb)     reset_kwb ;;
    reset-full)    reset_full ;;
    restart)       restart_container ;;
    logs)          show_logs ;;
    logs-kwb)      show_kwb_logs ;;
    status)        show_status ;;
    open)          open_ha ;;
    backup-config) backup_config ;;
    help)          show_help ;;
    *)
        echo -e "${RED}❌ Unknown action: ${action}${NC}"
        show_help
        exit 1
        ;;
esac
