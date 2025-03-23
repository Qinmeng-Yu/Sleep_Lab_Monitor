from pymodm import fields, MongoModel


class CPAPdata(MongoModel):
    cpap_pressure = fields.IntegerField()
    breathing_rate = fields.FloatField(blank=True)
    apnea_count = fields.IntegerField(blank=True)
    flow_image_base64 = fields.CharField(blank=True)
    timestamp = fields.DateTimeField()


class Patient(MongoModel):
    mrn = fields.IntegerField(primary_key=True)
    name = fields.CharField()
    room = fields.IntegerField()
    data = fields.ListField(fields.EmbeddedDocumentField(CPAPdata), blank=True)
