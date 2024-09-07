FROM financial-analysis-base-image

EXPOSE 8501
ENV PYTHONBUFFERED 1

CMD ["/usr/bin/supervisord"]
CMD ["streamlit", "run","streamlit_app/app.py"]
