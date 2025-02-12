"""
WEBVTT
Video Text Track

Basically all captions, be it closed caption
or transcripts of meetings.

NOTE: at this time, the format support is minimal.
It is foruced mostly on reading meeting transcripts.

See:
https://w3c.github.io/webvtt/
And there is also a browser api:
https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API
"""
import typing
import datetime
from paths import UrlCompatible,asUrl


class PersonalName:
    """
    A string representing a person's name
    """
    def __init__(self,name:str):
        self.firstName:str=''
        self.lastName:str=''
        self.middleName:str=''
        self.assign(name)

    @property
    def first(self)->str:
        """
        the first name
        """
        return self.firstName
    @first.setter
    def first(self,first:str):
        self.firstName=first

    def contains(self,m:str)->bool:
        """
        Check to see if it contains a given substring
        """
        m=m.lower()
        if self.firstName.lower().find(m)>=0:
            return True
        if self.lastName.lower().find(m)>=0:
            return True
        if self.middleName.lower().find(m)>=0:
            return True
        return False

    def matches(self,other:typing.Union["PersonalName",str])->float:
        """
        returns a rank of how well this matches another name:
            0.0 = cannot be the other name
            0.5 = 50/50 chance that it could be the other name
            1.0 = 100% sure it matches the other name
        """
        if not isinstance(other,PersonalName):
            other=PersonalName(other)
        def getMemberRank(memberName:str):
            us=getattr(self,memberName).lower()
            them=getattr(other,memberName).lower()
            if not us or not them:
                return 0.5
            if us==them:
                return 1.0
            return 0.0
        rank=getMemberRank("firstName")\
            *getMemberRank("middleName")\
            *getMemberRank("lastName")
        return rank

    def __eq__(self,other:typing.Union["PersonalName",str])->float:
        """
        requires a matches() score of 80% or better
        """
        return self.matches(other)>=0.8

    def assign(self,name:str):
        """
        This can handle:
            "Eddy Murphy"
            "Murphy, Eddy"
            "Eddy James Murphy"
            "Murphy, Eddy James"
            "Murphy, Eddy J."
            etc
        """
        self.firstName=''
        self.middleName=''
        self.lastName=''
        name=name.strip()
        if not name:
            return
        commaSplit=name.split(',')
        if len(commaSplit)>1:
            if len(commaSplit)>2:
                raise Exception(f'Unrecognized name format "{name}"')
            self.lastName=commaSplit[0].strip()
            first_middle=commaSplit[1].strip().split(' ',1)
            self.firstName=first_middle[0].strip()
            if len(first_middle)>1:
                self.middleName=first_middle[1].replace('.',' ').strip()
        else:
            parts=commaSplit[0].split()
            self.firstName=parts[0]
            if len(parts)>1:
                self.lastName=parts[-1]
                if len(parts)>2:
                    self.middleName=\
                        (' '.join(parts[1:-1])).replace('.',' ').strip()
        #raise Exception(f'{self.firstName} | {self.middleName} | {self.lastName}') # debugging tool # noqa: E501 # pylint: disable=line-too-long

    @property
    def middleInitial(self)->str:
        """
        The person's middle initial (if there is one)
        """
        if self.middleName:
            return self.middleName[0]
        return ''
    mi=middleInitial

    @property
    def lastNameFirstName(self)->str:
        """
        The name in Last, First format
        """
        return f'{self.lastName}, {self.firstName}'

    def __repr__(self)->str:
        return f'{self.firstName}'


class TimestampedString:
    """
    A string containing a timestamp
    """

    def __init__(self,
        s:str,
        start:datetime.time,
        end:datetime.time,
        speaker:typing.Union[str,PersonalName]='',
        vttString:typing.Optional[str]=None):
        """ """
        self.s=s
        self.start=start
        self.end=end
        self._speaker:PersonalName
        self.speaker=speaker
        if vttString is not None:
            self.vttString=vttString

    @property
    def speaker(self)->PersonalName:
        """
        The person speaking
        """
        return self._speaker
    @speaker.setter
    def speaker(self,speaker:typing.Union[str,PersonalName]):
        if not isinstance(speaker,PersonalName):
            speaker=PersonalName(speaker)
        self._speaker=speaker

    @property
    def vttString(self)->str:
        """
        Get this as  a vtt string format
        """
        s=self.s.replace('\n',' ').replace('<',' less than ')
        return f'{self.start} --> {self.end}\n<v {self.speaker}>{s}</v>'
    @vttString.setter
    def vttString(self,vttString:str):
        lines=vttString.strip().split('\n')
        fmt="%H:%M:%S.%f"
        self.start,self.end=[
            datetime.datetime.strptime(x.strip(),fmt).time()
            for x in lines[0].split('-->')]
        name_text=lines[1].split('>',1)
        self.speaker=name_text[0].split('<v',1)[-1].strip()
        self.s=name_text[1].rsplit('<',1)[0].strip()

    def __repr__(self):
        return f'{self.speaker} said, "{self.s}"'


class VttFormat:
    """
    WEBVTT
    Video Text Track

    Basically all captions, be it closed caption
    or transcripts of meetings.

    NOTE: at this time, the format support is minimal.
    It is foruced mostly on reading meeting transcripts.

    See:
    https://w3c.github.io/webvtt/
    And there is also a browser api:
    https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API
    """
    def __init__(self,
        url:typing.Optional[UrlCompatible]=None,
        vttString:typing.Optional[str]=None):
        """ """
        self.entries:typing.List[TimestampedString]=[]
        if vttString is not None:
            self.vttString=vttString
        elif url is not None:
            self.load(url)

    def load(self,url:UrlCompatible)->None:
        """
        Load a .vtt file
        """
        self.entries:typing.List[TimestampedString]=[]
        self.vttString=asUrl(url).read()

    def save(self,url:UrlCompatible)->None:
        """
        Save as a .vtt file
        """
        asUrl(url).write(self.vttString)

    @property
    def vttString(self)->str:
        """
        Get as a .vtt string
        """
        ret=['WEBVTT']
        for entry in self.entries:
            ret.append(entry.vttString)
        return '\n\n'.join(ret)
    @vttString.setter
    def vttString(self,s:str):
        isVtt=False
        for line in s.replace('\r','').split('\n\n'):
            line=line.strip()
            if not isVtt:
                if line!='WEBVTT':
                    raise Exception("This doesn't appear to be VTT format (doesn't start with \"WEBVTT\")") # noqa: E501 # pylint: disable=line-too-long
                isVtt=True
                continue
            defaultTime=datetime.time()
            newTsString=TimestampedString(
                '',defaultTime,defaultTime,vttString=line)
            self.entries.append(newTsString)

    def __repr__(self):
        ret=[repr(entry) for entry in self.entries]
        return '\n\n'.join(ret)
