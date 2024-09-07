FROM financial-analysis-base-image

EXPOSE 5000
ENV PYTHONBUFFERED 1

CMD ["/usr/bin/supervisord"]
CMD ["python", "template_for_api_marketplace.py"]
