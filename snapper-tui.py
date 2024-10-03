import curses
import subprocess
import os

FILE_EXTENSION = '.ctl'

def get_snapper_configs():
    """snapper list-configs komutunu çalıştırarak konfigürasyonları alır."""
    result = subprocess.run(['snapper', 'list-configs'], capture_output=True, text=True)
    lines = result.stdout.splitlines()

    configs = [line.split('|')[0].strip() for line in lines[2:] if line.strip()]
    return configs

def get_snapshots_for_config(config):
    """Belirli bir config için snapshotları alır ve ayrı dosyaya yazar."""
    result = subprocess.run(['sudo', 'snapper', '-c', config, 'list'], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    
    filename = f"{config}{FILE_EXTENSION}"
    
    # Dosyayı oluştur ve snapshot bilgilerini yaz
    with open(filename, 'w') as file:
        file.write(result.stdout)

def read_snapshots_from_file(config):
    """Dosyadan snapshot bilgilerini okur ve değişkenlere atar."""
    snapshots = []
    filename = f"{config}{FILE_EXTENSION}"
    
    if not os.path.exists(filename):
        return snapshots
    
    with open(filename, 'r') as file:
        lines = file.readlines()
        
        # Başlıkları ve separator'ı atla
        header_line = lines[0].strip()
        separator_line = lines[1].strip()
        
        for line in lines[2:]:
            line = line.strip()
            if line:
                parts = line.split('|')
                if len(parts) >= 7:
                    snap_id = parts[0].strip()
                    snap_type = parts[1].strip()
                    snap_pre = parts[2].strip()
                    snap_date = parts[3].strip()
                    snap_user = parts[4].strip()
                    snap_cleanup = parts[5].strip()
                    snap_desc = parts[6].strip()
                    
                    snapshots.append({
                        'id': snap_id,
                        'type': snap_type,
                        'pre': snap_pre,
                        'date': snap_date,
                        'user': snap_user,
                        'cleanup': snap_cleanup,
                        'desc': snap_desc
                    })
                    
    return snapshots


def print_menu(stdscr, selected_config_index, selected_snapshot, snapshot_list, selected_option):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Başlıkları ekrana yazdır
    stdscr.addstr(0, 0, f"{'ID':<3} {'Type':<6} {'Pre':<5} {'Date':<25} {'User':<5} {'Cleanup':<7} {'Description':<30}")

    global config_name
    config_name = configs[selected_config_index]
    
    if config_name in snapshot_list:
        for idx, snap in enumerate(snapshot_list[config_name]):
            # Satırın rengini ayarla
            if snap['id'] == selected_snapshot:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 1, 0, f"{snap['id']:<3} {snap['type']:<6} {snap['pre']:<5} {snap['date']:<25} {snap['user']:<5} {snap['cleanup']:<7} {snap['desc']:<30}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"{snap['id']:<3} {snap['type']:<6} {snap['pre']:<5} {snap['date']:<25} {snap['user']:<5} {snap['cleanup']:<7} {snap['desc']:<30}")

    # Yönetim seçeneklerini ekranın altına yan yana yerleştir
    options = ['Config', 'Create', 'Remove', 'Rollback']
    option_width = w // len(options)  # Her seçeneğin genişliği
    for idx, option in enumerate(options):
        x = idx * option_width
        if idx == selected_option:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(h - 2, x, option.center(option_width))
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(h - 2, x, option.center(option_width))

    stdscr.refresh()

def show_message(stdscr, message):
    h, w = stdscr.getmaxyx()
    win = curses.newwin(5, w - 4, h // 2 - 2, 2)
    win.box()
    win.addstr(1, 1, message)
    win.refresh()
    win.getch()

def get_input(stdscr, prompt):
    h, w = stdscr.getmaxyx()
    win = curses.newwin(3, w - 4, h // 2 - 1, 2)
    win.box()
    win.addstr(1, 1, prompt)
    curses.echo()
    input_str = win.getstr(1, len(prompt) + 1, 20).decode("utf-8")
    curses.noecho()
    return input_str

def select_config(stdscr, configs, selected_config_index):
    curses.curs_set(0)  # Karakter imlecini gizler
    curses.start_color()  # Renkleri başlatır
    curses.init_color(1, 0, 0, 0)
    curses.init_pair(1, 1, curses.COLOR_WHITE)  # Renk çiftini tanımlar

    h, w = stdscr.getmaxyx()
    win_height = min(10, len(configs) + 2)
    win_width = w - 4
    win = curses.newwin(win_height, win_width, h // 2 - win_height // 2, 2)
    
    while True:
        win.clear()  # Pencereyi temizle
        win.box()  # Çerçeve çiz
        
        # Başlık
        stdscr.clear()
        win.addstr(0, (win_width - len("Select a config:")) // 2, "Select a config:")
        stdscr.refresh()
        
        # Konfigürasyonları göster
        for idx, config in enumerate(configs):
            if idx == selected_config_index:
                win.attron(curses.color_pair(1))
            win.addstr(idx + 1, (win_width - len(config)) // 2, config)
            if idx == selected_config_index:
                win.attroff(curses.color_pair(1))

        # Bilgilendirme metnini ekranın altına ekle
        info_text = (
            "Use the following keys to navigate this screen:\n"
            "- 'W' to move up\n"
            "- 'S' to move down\n"
            "- Alternatively, you can use '2' and '8' on the Numpad for navigation"
        )
        info_lines = info_text.split('\n')
        
        # Bilgilendirme metnini ekranın altında, border'ın dışına hizala
        for idx, line in enumerate(info_lines):
            stdscr.addstr(h // 2 + win_height // 2 + 1 + idx, 2, line)
        
        stdscr.refresh()
        win.refresh()

        key = win.getch()
        if key == ord('s'):
            selected_config_index = (selected_config_index + 1) % len(configs)
        elif key == ord('w'):
            selected_config_index = (selected_config_index - 1) % len(configs)
        elif key == ord('2'):
            selected_config_index = (selected_config_index + 1) % len(configs)
        elif key == ord('8'):
            selected_config_index = (selected_config_index - 1) % len(configs)
        elif key == 10:  # Enter tuşu
            break
        elif key == ord('q'):  # 'q' tuşu ile çıkış
            return None

    return selected_config_index

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    #stdscr.bkgd(' ', curses.color_pair("#000000"))

    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Konfigürasyonları al ve snapshot bilgilerini dosyalara yaz
    global configs, snapshots
    configs = get_snapper_configs()

    for config in configs:
        filename = f"{config}{FILE_EXTENSION}"
        if os.path.exists(filename):
            os.remove(filename)

    for config in configs:
        get_snapshots_for_config(config)

    # Dosyadan snapshot bilgilerini oku
    snapshots = {config: read_snapshots_from_file(config) for config in configs}

    selected_config_index = 0
    selected_snapshot = []
    selected_option = 0

    while True:
        print_menu(stdscr, selected_config_index, selected_snapshot, snapshots, selected_option)
        
        key = stdscr.getch()
        if key == ord('q'):  # 'q' tuşu ile çıkış
            break
        elif key == curses.KEY_LEFT:
            selected_option = (selected_option - 1) % 4  # 4 seçenek var
        elif key == curses.KEY_RIGHT:
            selected_option = (selected_option + 1) % 4  # 4 seçenek var
        elif key == curses.KEY_ENTER or key == 10:  # Enter tuşu ile seçim yapma
            if selected_option == 0:  # Config seçme
                new_config_index = select_config(stdscr, configs, selected_config_index)
                if new_config_index is not None:
                    selected_config_index = new_config_index
                    snapshots = {config: read_snapshots_from_file(config) for config in configs}
            elif selected_option == 1:  # Create snapshot   
                if configs[selected_config_index]:
                    desc = get_input(stdscr, "Enter snapshot description:")
                    subprocess.run(["sudo", "snapper", "-c", config_name, "create", "--description", desc])
                    get_snapshots_for_config(config_name)
                    snapshots = {config: read_snapshots_from_file(config) for config in configs}
                    stdscr.refresh()
                    show_message(stdscr, "Snapshot created successfully.")
            elif selected_option == 2:  # Remove snapshot
                    number = get_input(stdscr, "Enter snapshot ID:")
                    subprocess.run(["sudo", "snapper", "-c", config_name, "remove", number])
                    get_snapshots_for_config(config_name)
                    snapshots = {config: read_snapshots_from_file(config) for config in configs}
                    stdscr.refresh()
                    show_message(stdscr, "Snapshot removed successfully.")
            elif selected_option == 3:  # Rollback snapshot
                if selected_snapshot != -1 and configs[selected_config_index]:
                    # Rollback işlemi
                    numb = get_input(stdscr, "Enter snapshot ID:")
                    subprocess.run(["sudo", "snapper", "-c", config_name, "rollback", numb])
                    show_message(stdscr, f"You have rolled back to the snapshot with ID {numb}. A restart is required.")

curses.wrapper(main)
