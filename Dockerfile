FROM jupyter/minimal-notebook:abdb27a6dfbb

RUN pip install s3contents --no-cache-dir
RUN jupyter notebook --generate-config -y
COPY jupyter_notebook_config.py $HOME/.jupyter/jupyter_notebook_config.py
