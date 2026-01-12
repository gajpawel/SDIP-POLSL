from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Interval, Float, Boolean, Date
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, date

class Administrator(Base):
    __tablename__ = "administrator"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # zahashowane hasło
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    station_id = Column(Integer, ForeignKey("station.id"), nullable=False)

    role = relationship("Role")
    station = relationship("Station")

class Carrier(Base):
    __tablename__ = "carrier"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=True)
    timezone = Column(String, nullable=True)

class Calendar(Base):
    __tablename__ = "calendar"
    service_id = Column(Integer, primary_key=True, index=True)
    monday = Column(Boolean, default=True)
    tuesday = Column(Boolean, default=True)
    wednesday = Column(Boolean, default=True)
    thursday = Column(Boolean, default=True)
    friday = Column(Boolean, default=True)
    saturday = Column(Boolean, default=True)
    sunday = Column(Boolean, default=True)
    start_date = Column(Date) # Pierwszy dzień ważności rozkładu
    end_date = Column(Date) # Ostatni dzień ważności rozkładu

    # Sprawdza, czy pociąg kursuje danego dnia
    def runs_on_date(self, target_date: date):
        # Sprawdzanie zakresu ważności rozkładu
        if not (self.start_date <= target_date <= self.end_date):
            return False
        days_mask = (
            (1 if self.monday else 0) |
            (2 if self.tuesday else 0) |
            (4 if self.wednesday else 0) |
            (8 if self.thursday else 0) |
            (16 if self.friday else 0) |
            (32 if self.saturday else 0) |
            (64 if self.sunday else 0)
        )
        # Sprawdzanie dnia tygodnia (0=Pn, 6=Nd)
        weekday = target_date.weekday()
        return bool(days_mask & (1 << weekday))

class Display(Base):
    __tablename__ = "display"
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String, nullable=True)
    type_id = Column(Integer, ForeignKey("display_type.id"), nullable=False)
    station_id = Column(Integer, ForeignKey("station.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platform.id"), nullable=True)
    track_id = Column(Integer, ForeignKey("track.id"), nullable=True)
    main_color = Column(String, nullable=False)
    background_color = Column(String, nullable=False)
    theme = Column(Boolean, nullable=False)
    font = Column(String, nullable=False)
    intermediates_number = Column(Integer, nullable=True)


    type = relationship("DisplayType")
    station = relationship("Station")
    platform = relationship("Platform")
    track = relationship("Track")
    
class DisplayType(Base):
    __tablename__ = "display_type"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    picture_path = Column(String, nullable=False)

class Platform(Base):
    __tablename__ = "platform"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("station.id"), nullable=False)
    number = Column(String, nullable=False)

    station = relationship("Station")

class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Route(Base):
    __tablename__ = "route"
    id = Column(String, primary_key=True)
    train_number = Column(String, nullable=False)
    carrier_id = Column(Integer, ForeignKey("carrier.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("route_type.id"), nullable=False)
    final_station_id = Column(Integer, ForeignKey("station.id"), nullable=False)

    carrier = relationship("Carrier")
    type = relationship("RouteType")
    final_station = relationship("Station", foreign_keys=[final_station_id])

class RouteType(Base):
    __tablename__ = "route_type"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

class Station(Base):
    __tablename__ = "station"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    voice_model_id = Column(String, ForeignKey("voice_model.id"), nullable=True)
    voice_stability = Column(Integer, nullable=True)
    voice_similarity = Column(Integer, nullable=True)
    voice_style = Column(String, nullable=True)

    voice_model = relationship("VoiceModel")

class Stop(Base):
    __tablename__ = "stop"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(String, ForeignKey("trip.trip_id"), nullable=False)
    original_track_id = Column(Integer, ForeignKey("track.id"), nullable=False)
    arrival = Column(DateTime, nullable=True)
    departure = Column(DateTime, nullable=True)
    sequence = Column(Integer, nullable=False)

    trip = relationship("Trip")
    original_track = relationship("Track", foreign_keys=[original_track_id])
    statuses = relationship("StopStatus", back_populates="stop")

class StopStatus(Base):
    """
    Tabela przechowująca TYLKO zmiany w stosunku do planu dla konkretnego dnia.
    Jeśli pociąg jedzie idealnie, rekord dla danej daty może nie istnieć.
    """
    __tablename__ = 'stop_status'
    id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(ForeignKey('stop.id'))
    date = Column(Date, default=date.today) # Kluczowe: Status przypisany do dnia
    
    arrival_delay = Column(Integer, default=0)
    departure_delay = Column(Integer, default=0)
    track_id = Column(Integer, ForeignKey("track.id"), nullable=True)
    is_cancelled = Column(Boolean, default=False)
    bus = Column(Boolean, default=False)

    stop = relationship("Stop")
    track = relationship("Track", foreign_keys=[track_id])
    stop = relationship("Stop", back_populates="statuses")

class Track(Base):
    __tablename__ = "track"
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platform.id"), nullable=False)
    number = Column(String, nullable=False)

    platform = relationship("Platform")

class Trip(Base):
    __tablename__ = "trip"
    trip_id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("route.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("calendar.service_id"), nullable=False)

    route = relationship("Route")
    calendar = relationship("Calendar", foreign_keys=[service_id])

class VoiceModel(Base):
    __tablename__ = "voice_model"
    id = Column(Integer, primary_key=True, index=False)
    name = Column(String, nullable=False)