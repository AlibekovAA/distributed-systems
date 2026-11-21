export function createEmptyStateIcon(): HTMLElement {
    const icon = document.createElement('div');
    icon.className = 'state-icon';
    icon.setAttribute('aria-hidden', 'true');

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.8');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');

    const bag = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    bag.setAttribute('d', 'M5 8h14l-1 12H6L5 8Z');
    const handle = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    handle.setAttribute('d', 'M9 9V6a3 3 0 0 1 6 0v3');
    svg.append(bag, handle);
    icon.appendChild(svg);
    return icon;
}
