"""
Configuration utilities for Win9xManager
"""

import configparser
import string
from pathlib import Path

def create_default_template(templates_dir):
    """Create the default DOSBox-X template file"""
    template_path = templates_dir / "dosbox_template.conf"
    
    # Make sure templates directory exists
    templates_dir.mkdir(exist_ok=True, parents=True)
    
    # Write template content
    with open(template_path, 'w') as f:
        f.write("""# DOSBox-X configuration file for Windows 9x Manager

[sdl]
fullscreen=false
fulldouble=true
fullresolution=desktop
windowresolution=${windowresolution}
output=${output}
autolock=true

[dosbox]
language=
machine=${machine}
captures=capture
memsize=${memsize}

[render]
frameskip=0
aspect=true
scaler=normal3x

[cpu]
core=dynamic
cputype=pentium_mmx
cycles=${cycles}
cycleup=500
cycledown=500

[mixer]
nosound=false
rate=44100
blocksize=1024
prebuffer=40

[midi]
mpu401=intelligent
mididevice=default

[sblaster]
sbtype=sb16
sbbase=220
irq=7
dma=1
hdma=5
sbmixer=true
oplmode=auto
oplemu=default
oplrate=44100

[gus]
gus=false
gusrate=44100
gusbase=240
irq1=5
dma1=1

[speaker]
pcspeaker=true
pcrate=44100
tandy=auto
tandyrate=44100
disney=true

[dos]
xms=true
ems=true
umb=true
keyboardlayout=auto

[ipx]
ipx=false
""")

def generate_config_from_template(templates_dir, template_name, output_path, variables):
    """Generate a configuration file from a template with variable substitution
    
    Args:
        templates_dir: Directory containing templates
        template_name: Name of the template file in templates directory
        output_path: Path where to save the generated config
        variables: Dictionary of variables to substitute in the template
    """
    template_path = templates_dir / template_name
    
    # Read template content
    if not template_path.exists():
        raise FileNotFoundError(f"Template file {template_path} not found")
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Use string.Template for variable substitution
    template = string.Template(template_content)
    output_content = template.safe_substitute(variables)
    
    # Write the output file
    with open(output_path, 'w') as f:
        f.write(output_content)

def create_temp_config(dosbox_conf, autoexec_content, templates_dir, base_dir):
    """Create a temporary DOSBox-X configuration file with custom autoexec section"""
    # Make sure the base config exists
    if not dosbox_conf.exists():
        # Create default config
        config_dir = base_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Check if template exists
        template_path = templates_dir / "dosbox_template.conf"
        if not template_path.exists():
            create_default_template(templates_dir)
        
        # Create config from template
        template_vars = {
            'memsize': '64',
            'cycles': 'max 80% limit 33000',
            'machine': 'svga_s3',
            'windowresolution': '1024x768',
            'output': 'opengl'
        }
        generate_config_from_template(templates_dir, 'dosbox_template.conf', dosbox_conf, template_vars)
    
    # Create a temp config based on current settings
    temp_conf = base_dir / "temp_dosbox.conf"
    
    # Read current config to preserve settings
    current_config = {}
    config = configparser.ConfigParser()
    config.read(dosbox_conf)
    
    for section in config.sections():
        if section != 'autoexec':
            current_config[section] = dict(config[section])
    
    # Generate the temporary config file from template
    template_vars = {
        'memsize': current_config.get('dosbox', {}).get('memsize', '64'),
        'cycles': current_config.get('cpu', {}).get('cycles', 'max 80% limit 33000'),
        'machine': current_config.get('dosbox', {}).get('machine', 'svga_s3'),
        'windowresolution': current_config.get('sdl', {}).get('windowresolution', '1024x768'),
        'output': current_config.get('sdl', {}).get('output', 'opengl')
    }
    
    # Create temp config
    generate_config_from_template(templates_dir, 'dosbox_template.conf', temp_conf, template_vars)
    
    # Add autoexec section to the generated config
    with open(temp_conf, 'a') as f:
        f.write("\n[autoexec]\n")
        for line in autoexec_content.split('\n'):
            if line.strip():
                f.write(f"{line}\n")
    
    return temp_conf
