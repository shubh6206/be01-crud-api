import os, hashlib, zlib, time

class PyGitRepo:
    def __init__(self, repo_dir, author="Shubham Kumar <shubham.kumar@smit.edu.in>"):
        self.repo_dir = os.path.abspath(repo_dir)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        self.author = author
        self.head_commit = self._get_current_head()
        self._init_repo()

    def _init_repo(self):
        os.makedirs(os.path.join(self.git_dir, "objects"), exist_ok=True)
        os.makedirs(os.path.join(self.git_dir, "refs", "heads"), exist_ok=True)
        head_file = os.path.join(self.git_dir, "HEAD")
        if not os.path.exists(head_file):
            with open(head_file, "w") as f:
                f.write("ref: refs/heads/main\n")

    def _get_current_head(self):
        ref_path = os.path.join(self.git_dir, "refs", "heads", "main")
        if os.path.exists(ref_path):
            with open(ref_path, "r") as f:
                return f.read().strip()
        return None

    def _write_object(self, obj_type, content_bytes):
        header = f"{obj_type} {len(content_bytes)}\x00".encode('utf-8')
        store = header + content_bytes
        sha1 = hashlib.sha1(store).hexdigest()
        obj_path = os.path.join(self.git_dir, "objects", sha1[:2], sha1[2:])
        if not os.path.exists(obj_path):
            os.makedirs(os.path.dirname(obj_path), exist_ok=True)
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(store))
        return sha1

    def _write_blob(self, file_path):
        with open(file_path, "rb") as f:
            content = f.read()
        return self._write_object("blob", content)

    def _write_tree_recursive(self, current_dir):
        entries = []
        for name in sorted(os.listdir(current_dir)):
            if name in [".git", "__pycache__", "git_manager.py", "run_server.py"] or name.endswith(".pyc"):
                continue
            full_path = os.path.join(current_dir, name)
            if os.path.isfile(full_path):
                mode = "100644" if not os.access(full_path, os.X_OK) else "100755"
                sha1_hex = self._write_blob(full_path)
                sha1_bytes = bytes.fromhex(sha1_hex)
                entry = f"{mode} {name}\x00".encode('utf-8') + sha1_bytes
                entries.append(entry)
            elif os.path.isdir(full_path):
                sub_sha1_hex = self._write_tree_recursive(full_path)
                sha1_bytes = bytes.fromhex(sub_sha1_hex)
                entry = f"40000 {name}\x00".encode('utf-8') + sha1_bytes
                entries.append(entry)
        
        tree_bytes = b"".join(entries)
        return self._write_object("tree", tree_bytes)

    def commit(self, message, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())
        tree_sha1 = self._write_tree_recursive(self.repo_dir)
        
        lines = [f"tree {tree_sha1}"]
        if self.head_commit:
            lines.append(f"parent {self.head_commit}")
        lines.append(f"author {self.author} {timestamp} +0000")
        lines.append(f"committer {self.author} {timestamp} +0000")
        lines.append("")
        lines.append(message)
        lines.append("")
        
        commit_bytes = "\n".join(lines).encode('utf-8')
        commit_sha1 = self._write_object("commit", commit_bytes)
        
        ref_path = os.path.join(self.git_dir, "refs", "heads", "main")
        with open(ref_path, "w") as f:
            f.write(commit_sha1 + "\n")
        
        self.head_commit = commit_sha1
        print(f"✅ Committed [{commit_sha1[:7]}]: {message}")
        return commit_sha1

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Update repository"
    repo = PyGitRepo("/working_dir/be01-crud-api")
    repo.commit(msg)
