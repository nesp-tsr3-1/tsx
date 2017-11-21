# coding: utf-8
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class GridCell(Base):
    __tablename__ = 'grid_cell'

    id = Column(Integer, primary_key=True)
    x = Column(Float(asdecimal=True))
    y = Column(Float(asdecimal=True))
    grid_size_in_degrees = Column(Float(asdecimal=True))


class IncidentalSighting(Base):
    __tablename__ = 'incidental_sighting'

    taxon_id = Column(String(6), primary_key=True)
    coords = Column(NullType)
    date = Column(Date)


class Range(Base):
    __tablename__ = 'range'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class ResponseVariableType(Base):
    __tablename__ = 'response_variable_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class SearchType(Base):
    __tablename__ = 'search_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


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
    description = Column(String(255), nullable=False)


t_species_presence = Table(
    'species_presence', metadata,
    Column('spno', SmallInteger, server_default=text("'0'")),
    Column('coords', NullType)
)


class SpeciesRange(Base):
    __tablename__ = 'species_range'

    species_id = Column(Integer, primary_key=True)


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    geometry = Column(NullType)


class T1Sighting(Base):
    __tablename__ = 't1_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't1_survey.id'), nullable=False, index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey(u'unit.id'), nullable=False, index=True)
    breeding = Column(Integer)

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
    start_date_d = Column(SmallInteger)
    start_date_m = Column(SmallInteger)
    start_date_y = Column(SmallInteger, nullable=False)
    finish_date_d = Column(SmallInteger)
    finish_date_m = Column(SmallInteger)
    finish_date_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    coords = Column(NullType)
    location = Column(Text)
    positional_accuracy_in_m = Column(Float(asdecimal=True))
    comments = Column(Text)
    response_variable_type_id = Column(ForeignKey(u'response_variable_type.id'), index=True)

    response_variable_type = relationship(u'ResponseVariableType')
    site = relationship(u'T1Site')
    source = relationship(u'Source')


class T2Sighting(Base):
    __tablename__ = 't2_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't2_survey.id'), nullable=False, index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True))
    unit_id = Column(ForeignKey(u'unit.id'), index=True)
    breeding = Column(Integer)

    survey = relationship(u'T2Survey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T2Site(Base):
    __tablename__ = 't2_site'

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(u'source.id'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    geometry = Column(NullType)

    search_type = relationship(u'SearchType')
    source = relationship(u'Source')
    surveys = relationship(u'T2Survey', secondary='t2_survey_site')


class T2Suitability(Base):
    __tablename__ = 't2_suitability'

    taxon_id = Column(Integer, primary_key=True)
    experimental_design_type_id = Column(Integer)
    response_variable_type_id = Column(Integer)
    is_suitable = Column(Integer)


class T2Survey(Base):
    __tablename__ = 't2_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey(u't2_site.id'), index=True)
    source_id = Column(ForeignKey(u'source.id'), nullable=False, index=True)
    start_date_d = Column(SmallInteger)
    start_date_m = Column(SmallInteger)
    start_date_y = Column(SmallInteger, nullable=False)
    finish_date_d = Column(SmallInteger)
    finish_date_m = Column(SmallInteger)
    finish_date_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    coords = Column(NullType, nullable=False, index=True)
    location = Column(Text)
    positional_accuracy_in_m = Column(Float(asdecimal=True))
    comments = Column(Text)
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    source_primary_key = Column(String(255), nullable=False, unique=True)
    secondary_source_id = Column(String(255))

    search_type = relationship(u'SearchType')
    site = relationship(u'T2Site')
    source = relationship(u'Source')


t_t2_survey_site = Table(
    't2_survey_site', metadata,
    Column('survey_id', ForeignKey(u't2_survey.id'), primary_key=True, nullable=False),
    Column('site_id', ForeignKey(u't2_site.id'), primary_key=True, nullable=False, index=True)
)


class T2UltrataxonSighting(Base):
    __tablename__ = 't2_ultrataxon_sighting'

    sighting_id = Column(ForeignKey(u't2_sighting.id'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey(u'taxon.id'), primary_key=True, nullable=False, index=True)
    range_id = Column(ForeignKey(u'range.id'), nullable=False, index=True)
    generated_subspecies = Column(Integer, nullable=False)

    range = relationship(u'Range')
    sighting = relationship(u'T2Sighting')
    taxon = relationship(u'Taxon')


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
    population = Column(String(255))
    aust_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    epbc_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    iucn_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    bird_group = Column(String(255))

    aust_status = relationship(u'TaxonStatus', primaryjoin='Taxon.aust_status_id == TaxonStatus.id')
    epbc_status = relationship(u'TaxonStatus', primaryjoin='Taxon.epbc_status_id == TaxonStatus.id')
    iucn_status = relationship(u'TaxonStatus', primaryjoin='Taxon.iucn_status_id == TaxonStatus.id')
    taxon_level = relationship(u'TaxonLevel')


class TaxonHybrid(Base):
    __tablename__ = 'taxon_hybrid'

    id = Column(String(12), primary_key=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), index=True)

    taxon = relationship(u'Taxon')


class TaxonLevel(Base):
    __tablename__ = 'taxon_level'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


t_taxon_presence_alpha_hull = Table(
    'taxon_presence_alpha_hull', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False)
)


t_taxon_presence_alpha_hull_subdiv = Table(
    'taxon_presence_alpha_hull_subdiv', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False)
)


t_taxon_range = Table(
    'taxon_range', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey(u'range.id'), index=True),
    Column('geometry', NullType, nullable=False)
)


t_taxon_range_subdiv = Table(
    'taxon_range_subdiv', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey(u'range.id'), index=True),
    Column('geometry', NullType, nullable=False)
)


class TaxonStatus(Base):
    __tablename__ = 'taxon_status'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
