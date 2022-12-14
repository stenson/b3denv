import platform, re, os, sys, subprocess

def _os(): return platform.system()
def on_windows(): return _os() == "Windows"
def on_mac(): return _os() == "Darwin"
def on_linux(): return _os() == "Linux"

root = os.path.abspath(".")

def get_vars(addon_name):
    if addon_name:
        addon_source = os.path.join(root, addon_name)
    else:
        addon_source = None
    
    blender = os.environ.get("BLENDER_PATH")
    #blender = config.get("BLENDER")
    
    if not blender:
        if on_mac():
            blender = "/Applications/Blender.app/"

    blender = os.path.abspath(os.path.expanduser(blender))

    if on_mac():
        res = os.path.join(blender, "Contents/Resources")
        version = None
        for p in os.listdir(res):
            if os.path.isdir(os.path.join(res, p)):
                name = os.path.basename(p)
                if re.match(r"[23]{1}\.[0-9]{1,2}", name):
                    version = name
        
        addon_path = "".join(["~/Library/Application Support/Blender/", version, "/scripts/addons"])
        addon_path = os.path.abspath(os.path.expanduser(addon_path))
        if addon_name:
            addon = os.path.join(addon_path, addon_name)
        else:
            addon = None
        
        python_folder = os.path.join(blender, "Contents/Resources", version, "python/bin")
        python = None

        for f in os.listdir(python_folder):
            name = os.path.basename(f)
            if name.startswith("python"):
                python = os.path.join(python_folder, f)

        bpy = python

        blender_executable = os.path.join(blender, "Contents/MacOS/Blender")

        return {
            "addon_name": addon_name,
            "addon_source": addon_source,
            "addon_path": addon_path,
            "addon": addon,
            "bpy": bpy,
            "blender": blender_executable
        }


def fill_out_python(vars):
    bpy = vars.get("bpy")
    bpy_version = subprocess.check_output([bpy, "--version"]).split(" ")[-1].strip()

    #import urllib.request
    import shutil
    import sys
    import requests, tarfile, tempfile

    package = os.path.dirname(os.path.abspath(__file__))
    versions_folder = os.path.join(package, "versions")
    version_folder = os.path.join(versions_folder, bpy_version)
    if not os.path.exists(versions_folder):
        os.mkdir(versions_folder)
    if not os.path.exists(version_folder):
        os.mkdir(version_folder)

    def download(version):
        tgz = "".join(["https://www.python.org/ftp/python/", version, "/Python-", version, ".tgz"])
        print(tgz)
        response = requests.get(tgz, stream=True)
        
        file = tarfile.open(fileobj=response.raw, mode="r|gz")

        file.extractall(path=version_folder)
        src = os.path.join(version_folder, ("Python-" + version + "/Include"))
        dst_include = os.path.join(os.path.dirname(os.path.dirname(bpy)),  "include")
        dst = os.path.join(dst_include, os.listdir(dst_include)[0])

        for f in os.listdir(src):
            src_fp = os.path.join(src, f)
            dst_fp = os.path.join(dst, f)

            print("---")
            print(src_fp)
            print(dst_fp)

            if os.path.isdir(src_fp):
                shutil.copytree(src_fp, dst_fp)
            else:
                shutil.copy2(src_fp, dst_fp)

    download(bpy_version)
    print("done")


def install(vars):
    addon_source = vars.get("addon_source")
    addon = vars.get("addon")

    if on_mac():
        if os.path.exists(addon): os.unlink(addon)
        subprocess.call(["ln", "-s", addon_source, addon])
        print("SOURCE", addon_source)
        print("SYMLINK", addon)


def uninstall(vars):
    addon_source = vars.get("addon_source")
    addon = vars.get("addon")

    if on_mac():
        if os.path.exists(addon): os.unlink(addon)
        print("Uninstalled symlink:", addon)
        #subprocess.call(["ln", "-s", addon_source, addon])
        #print("SOURCE", addon_source)
        #print("SYMLINK", addon)


def release(vars):
    import zipfile, re

    addon_name = vars.get("addon_name")
    init = os.path.join(root, addon_name, "__init__.py")
    
    with open(init, "r") as f:
        version_match = re.search(r"\"version\"\:\s\(([0-9]{1}),\s?([0-9]{1,2})\)", f.read())
        #mj, mn = version_match[1], version_match[2]

    mj, mn = version_match.groups()

    releases = os.path.join(root, "_releases")

    if not os.path.exists(releases):
        os.mkdir(releases)

    release = os.path.join(releases, "ST2-v" + mj + "-" + mn + ".zip")
    if os.path.exists(release):
        os.unlink(release)

    zf = zipfile.ZipFile(release, "w")
    for file in os.listdir(addon_name):
        f = os.path.join(addon_name, file)
        if not os.path.isdir(f):
            print("> " + f)
            zf.write(f)
    zf.close()


def main():
    if len(sys.argv) == 1:
        print("b3denv <action> <extension-name>?")
        return

    action = sys.argv[1]
    if len(sys.argv) > 2:
        addon_name = sys.argv[2]
    else:
        addon_name = None
    
    vars = get_vars(addon_name)

    if action == "blender":
        sys.stdout.write(str(vars.get("blender")))
    elif action == "bpy":
        sys.stdout.write(str(vars.get("bpy")))
    elif action == "install":
        install(vars)
    elif action == "uninstall":
        uninstall(vars)
    elif action == "show":
        addon_path = vars.get("addon_path")
        subprocess.call(["open", addon_path])
    elif action == "release":
        release(vars)
    elif action == "download":
        fill_out_python(vars)
    else:
        print(f"Action ({action}) not recognized")


if __name__ == "__main__":
    main()