# coding: utf-8
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()
metadata = Base.metadata


class GridTaxonPresence(Base):
    __tablename__ = 'grid_taxon_presence'

    grid_size = Column(Integer, primary_key=True, nullable=False)
    grid_x = Column(Integer, primary_key=True, nullable=False)
    grid_y = Column(Integer, primary_key=True, nullable=False)
    taxon_id = Column(Integer)
    experimental_design_type_id = Column(Integer)


class IncidentalSighting(Base):
    __tablename__ = 'incidental_sighting'

    taxon_id = Column(String(6), primary_key=True)
    coords = Column(NullType)
    date = Column(Date)


class Range(Base):
    __tablename__ = 'range'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class SearchType(Base):
    __tablename__ = 'search_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class SiteTaxonPresence(Base):
    __tablename__ = 'site_taxon_presence'

    site_id = Column(Integer, primary_key=True)
    taxon_id = Column(Integer)


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    source_type_id = Column(ForeignKey(u'source_type.id'), index=True)
    provider = Column(String(255))
    description = Column(String(255))
    notes = Column(Text)

    source_type = relationship(u'SourceType')


class SourceType(Base):
    __tablename__ = 'source_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


t_species_presence = Table(
    'species_presence', metadata,
    Column('spno', SmallInteger, server_default=text("'0'")),
    Column('coords', Geometry)
)


class T1Sighting(Base):
    __tablename__ = 't1_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't1_survey.id'), nullable=False, index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey(u'unit.id'), nullable=False, index=True)

    survey = relationship(u'T1Survey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T1Site(Base):
    __tablename__ = 't1_site'

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(u'source.id'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    notes = Column(Text)

    search_type = relationship(u'SearchType')
    source = relationship(u'Source')


class T1Survey(Base):
    __tablename__ = 't1_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey(u't1_site.id'), nullable=False, index=True)
    source_id = Column(ForeignKey(u'source.id'), nullable=False, index=True)
    source_primary_key = Column(String(255), nullable=False, unique=True)
    start_d = Column(SmallInteger)
    start_m = Column(SmallInteger)
    start_y = Column(SmallInteger, nullable=False)
    finish_d = Column(SmallInteger)
    finish_m = Column(SmallInteger)
    finish_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    coords = Column(NullType)
    location = Column(String(255))
    positional_accuracy = Column(Float(asdecimal=True))
    comments = Column(Text)

    site = relationship(u'T1Site')
    source = relationship(u'Source')


class T2ProcessedSighting(Base):
    __tablename__ = 't2_processed_sighting'

    sighting_id = Column(ForeignKey(u't2_sighting.id'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey(u'taxon.id'), primary_key=True, nullable=False, index=True)
    range_id = Column(ForeignKey(u'range.id'), nullable=False, index=True)
    generated_subspecies = Column(Integer, nullable=False)

    range = relationship(u'Range')
    sighting = relationship(u'T2Sighting')
    taxon = relationship(u'Taxon')


class T2Sighting(Base):
    __tablename__ = 't2_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't2_survey.id'), index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), index=True)
    count = Column(Float(asdecimal=True))
    unit_id = Column(ForeignKey(u'unit.id'), index=True)

    survey = relationship(u'T2Survey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T2Site(Base):
    __tablename__ = 't2_site'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer)
    name = Column(String(255))
    search_type_id = Column(Integer)

    surveys = relationship(u'T2Survey', secondary='t2_survey_site')


class T2Survey(Base):
    __tablename__ = 't2_survey'

    id = Column(Integer, primary_key=True)
    source_Id = Column(ForeignKey(u'source.id'), nullable=False, index=True)
    start_d = Column(SmallInteger)
    start_m = Column(SmallInteger)
    start_y = Column(SmallInteger, nullable=False)
    finish_d = Column(SmallInteger)
    finish_m = Column(SmallInteger)
    finish_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    coords = Column(NullType)
    location = Column(String(255))
    position_accuracy = Column(Float(asdecimal=True))
    comments = Column(Text)
    search_type_id = Column(ForeignKey(u'search_type.id'), index=True)

    search_type = relationship(u'SearchType')
    source = relationship(u'Source')


t_t2_survey_site = Table(
    't2_survey_site', metadata,
    Column('survey_id', ForeignKey(u't2_survey.id'), primary_key=True, nullable=False),
    Column('site_id', ForeignKey(u't2_site.id'), primary_key=True, nullable=False, index=True)
)


class Taxon(Base):
    __tablename__ = 'taxon'

    id = Column(String(6), primary_key=True)
    ultrataxon = Column(Integer, nullable=False)
    taxon_level_id = Column(ForeignKey(u'taxon_level.id'), nullable=False, index=True)
    spno = Column(SmallInteger, nullable=False)
    common_name = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=False)
    family_common_name = Column(String(255))
    family_scientific_name = Column(String(255))
    order = Column(String(255))
    population = Column(Integer)
    australian_conservation_status = Column(String(255))
    include_for_nesp = Column(Integer, nullable=False, server_default=text("'1'"))

    taxon_level = relationship(u'TaxonLevel')


class TaxonPresenceAlphaHull(Taxon):
    __tablename__ = 'taxon_presence_alpha_hull'

    taxon_id = Column(ForeignKey(u'taxon.id'), primary_key=True)
    range_id = Column(ForeignKey(u'range.id'), index=True)
    breeding_range_id = Column(Integer)
    geometry = Column(NullType)

    range = relationship(u'Range')


class TaxonHybrid(Base):
    __tablename__ = 'taxon_hybrid'

    id = Column(String(12), primary_key=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), index=True)

    taxon = relationship(u'Taxon')


class TaxonLevel(Base):
    __tablename__ = 'taxon_level'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))
