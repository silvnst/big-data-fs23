import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError

def execute_notebooks(notebook_paths):
    #function to execute notebooks
    for notebook_path in notebook_paths:
        # open the notebook
        with open(notebook_path, 'r') as f:
            nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)
        ep = ExecutePreprocessor()
        # try to execute the notebook
        try:
            out = ep.preprocess(nb)
        except CellExecutionError:
            out = None
            msg = 'Error executing the notebook "%s".\n\n' % notebook_path
            msg += 'See notebook "%s" for the traceback.' % notebook_path
            print(msg)
            raise
        finally:
            with open(notebook_path, mode='w', encoding='utf-8') as f:
                nbformat.write(nb, f)

# Example
notebook_paths = ['feature_engineering_twitter.ipynb']
execute_notebooks(notebook_paths)
# Usage
# notebook_paths = ['data_scraping_sbb.ipynb', data_scraping_twitter.ipynb, 'feature_engineering_twitter.ipynb', 'feature_engineering.ipynb']
# execute_notebooks(notebook_paths)