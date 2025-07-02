import subprocess

def run():
    subprocess.run(['python', 'graph_builder/normalize.py'], check=True)
    subprocess.run(['python', 'graph_builder/build_graph.py'], check=True)

if __name__ == '__main__':
    run()
