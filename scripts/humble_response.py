#!/usr/bin/env python3
"""
TinyOwl Humble Response System
Implements theological humility with typed responses and source attribution
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json


class AuthorityLevel(Enum):
    """Levels of theological authority"""
    SCRIPTURE = "scripture"         # "Thus saith the Lord" - highest authority
    SOP = "sop"                    # Spirit of Prophecy - secondary authority  
    COMMENTARY = "commentary"       # Human commentary/sermons - interpretive
    ANALYSIS = "analysis"          # AI analysis - lowest authority
    UNKNOWN = "unknown"            # Uncertain source


class ConfidenceLevel(Enum):
    """Confidence in the response accuracy"""
    HIGH = "high"         # 90%+ confidence
    MEDIUM = "medium"     # 70-89% confidence  
    LOW = "low"          # 50-69% confidence
    UNCERTAIN = "uncertain"  # <50% confidence


@dataclass
class SourceCitation:
    """Individual source citation with metadata"""
    id: str
    osis_id: Optional[str]
    quote: str
    authority_level: AuthorityLevel
    confidence: ConfidenceLevel
    source_info: Dict[str, Any]  # book, chapter, author, work, etc.
    retrieval_score: float


@dataclass
class TypedResponse:
    """Complete typed response with humility levels"""
    query: str
    scripture_sources: List[SourceCitation]
    sop_sources: List[SourceCitation] 
    commentary_sources: List[SourceCitation]
    analysis: str
    overall_confidence: ConfidenceLevel
    caveats: List[str]
    cross_references: List[str]
    response_metadata: Dict[str, Any]


class HumbleResponseGenerator:
    """Generates responses with proper theological humility"""
    
    def __init__(self):
        self.authority_phrases = self._load_authority_phrases()
        self.humility_templates = self._load_humility_templates()
    
    def _load_authority_phrases(self) -> Dict[AuthorityLevel, List[str]]:
        """Load appropriate language for each authority level"""
        return {
            AuthorityLevel.SCRIPTURE: [
                "Scripture clearly states",
                "The Bible declares", 
                "God's Word says",
                "Scripture teaches",
                "The Bible affirms",
                "As written in Scripture"
            ],
            AuthorityLevel.SOP: [
                "Ellen White suggests",
                "The Spirit of Prophecy indicates", 
                "Ellen White writes",
                "According to the Spirit of Prophecy",
                "Ellen White explains",
                "The testimonies reveal"
            ],
            AuthorityLevel.COMMENTARY: [
                "The preacher argues",
                "The commentary suggests",
                "The author proposes", 
                "One interpretation holds",
                "The speaker explains",
                "This perspective suggests"
            ],
            AuthorityLevel.ANALYSIS: [
                "Analysis suggests",
                "It appears that",
                "This seems to indicate",
                "One possible understanding is",
                "The evidence points toward",
                "Based on the sources, it seems"
            ]
        }
    
    def _load_humility_templates(self) -> Dict[str, List[str]]:
        """Load humility language templates"""
        return {
            "uncertainty": [
                "This interpretation could be wrong",
                "Other perspectives may exist",
                "Further study is needed",
                "This understanding is not definitive",
                "Additional context may change this view"
            ],
            "interpretation": [
                "appears to indicate",
                "seems to suggest", 
                "may be understood as",
                "could be interpreted as",
                "might be seen as"
            ],
            "caveats": [
                "However, this is interpretive",
                "This goes beyond clear scriptural teaching",
                "Multiple views exist on this topic",
                "This represents one possible understanding",
                "Scripture doesn't explicitly address all aspects"
            ]
        }
    
    def create_typed_response(self, 
                            query: str,
                            search_results: List[Any],
                            ai_analysis: str = "") -> TypedResponse:
        """
        Create a typed response with proper source attribution
        
        Args:
            query: Original user query
            search_results: Results from retrieval system
            ai_analysis: AI-generated analysis text
        
        Returns:
            TypedResponse with proper humility levels
        """
        # Categorize sources by authority level
        scripture_sources = []
        sop_sources = []
        commentary_sources = []
        
        for result in search_results:
            citation = self._create_source_citation(result)
            
            if citation.authority_level == AuthorityLevel.SCRIPTURE:
                scripture_sources.append(citation)
            elif citation.authority_level == AuthorityLevel.SOP:
                sop_sources.append(citation)
            elif citation.authority_level == AuthorityLevel.COMMENTARY:
                commentary_sources.append(citation)
        
        # Determine overall confidence
        overall_confidence = self._calculate_overall_confidence(
            scripture_sources, sop_sources, commentary_sources
        )
        
        # Generate caveats based on source mix
        caveats = self._generate_caveats(
            scripture_sources, sop_sources, commentary_sources, overall_confidence
        )
        
        # Extract cross-references
        cross_references = self._extract_cross_references(search_results)
        
        return TypedResponse(
            query=query,
            scripture_sources=scripture_sources,
            sop_sources=sop_sources,
            commentary_sources=commentary_sources,
            analysis=ai_analysis,
            overall_confidence=overall_confidence,
            caveats=caveats,
            cross_references=cross_references,
            response_metadata={
                "source_count": len(search_results),
                "scripture_count": len(scripture_sources),
                "sop_count": len(sop_sources),
                "commentary_count": len(commentary_sources),
                "generation_timestamp": "2025-09-01"  # Could be dynamic
            }
        )
    
    def _create_source_citation(self, result: Any) -> SourceCitation:
        """Convert search result to source citation"""
        metadata = result.get('metadata', {})
        
        # Determine authority level from source
        authority_level = self._determine_authority_level(metadata)
        
        # Determine confidence from retrieval score and source type
        confidence = self._determine_confidence_level(
            result.get('score', 0.0), authority_level
        )
        
        return SourceCitation(
            id=result.get('id', ''),
            osis_id=metadata.get('osis_id'),
            quote=result.get('content', ''),
            authority_level=authority_level,
            confidence=confidence,
            source_info=self._extract_source_info(metadata),
            retrieval_score=result.get('score', 0.0)
        )
    
    def _determine_authority_level(self, metadata: Dict) -> AuthorityLevel:
        """Determine authority level from metadata"""
        source_type = metadata.get('type', '').lower()
        source_id = metadata.get('source_id', '').lower()
        
        # Scripture sources
        if (source_type == 'scripture' or 
            'bible' in source_id or 
            metadata.get('book_name') or
            metadata.get('osis_id')):
            return AuthorityLevel.SCRIPTURE
        
        # Spirit of Prophecy sources  
        if (source_type == 'sop' or
            'ellen' in source_id.lower() or
            'white' in source_id.lower() or
            'coa_' in source_id or  # Conflict of Ages series
            metadata.get('author', '').lower() in ['ellen g. white', 'ellen white']):
            return AuthorityLevel.SOP
        
        # Commentary sources (sermons, books, etc.)
        if (source_type in ['sermon', 'book', 'commentary'] or
            'sermon' in source_id):
            return AuthorityLevel.COMMENTARY
        
        return AuthorityLevel.UNKNOWN
    
    def _determine_confidence_level(self, 
                                  retrieval_score: float, 
                                  authority_level: AuthorityLevel) -> ConfidenceLevel:
        """Determine confidence based on score and authority"""
        # Base confidence from retrieval score
        if retrieval_score >= 0.8:
            base_confidence = ConfidenceLevel.HIGH
        elif retrieval_score >= 0.6:
            base_confidence = ConfidenceLevel.MEDIUM
        elif retrieval_score >= 0.4:
            base_confidence = ConfidenceLevel.LOW
        else:
            base_confidence = ConfidenceLevel.UNCERTAIN
        
        # Adjust based on authority level
        if authority_level == AuthorityLevel.SCRIPTURE:
            # Scripture gets confidence boost
            if base_confidence == ConfidenceLevel.MEDIUM:
                return ConfidenceLevel.HIGH
            elif base_confidence == ConfidenceLevel.LOW:
                return ConfidenceLevel.MEDIUM
        elif authority_level == AuthorityLevel.UNKNOWN:
            # Unknown sources get confidence penalty
            if base_confidence == ConfidenceLevel.HIGH:
                return ConfidenceLevel.MEDIUM
            elif base_confidence == ConfidenceLevel.MEDIUM:
                return ConfidenceLevel.LOW
        
        return base_confidence
    
    def _extract_source_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract relevant source information"""
        source_info = {}
        
        # Biblical sources
        if metadata.get('book_name'):
            source_info['book'] = metadata['book_name']
        if metadata.get('chapter_number'):
            source_info['chapter'] = metadata['chapter_number']
        if metadata.get('verse_numbers'):
            source_info['verses'] = metadata['verse_numbers']
        
        # Book sources
        if metadata.get('title'):
            source_info['work'] = metadata['title']
        if metadata.get('author'):
            source_info['author'] = metadata['author']
        if metadata.get('year'):
            source_info['year'] = metadata['year']
        
        return source_info
    
    def _calculate_overall_confidence(self,
                                    scripture_sources: List[SourceCitation],
                                    sop_sources: List[SourceCitation], 
                                    commentary_sources: List[SourceCitation]) -> ConfidenceLevel:
        """Calculate overall response confidence"""
        
        # High confidence if we have high-confidence scripture
        if any(s.confidence == ConfidenceLevel.HIGH for s in scripture_sources):
            return ConfidenceLevel.HIGH
        
        # Medium confidence if we have scripture + SOP agreement
        if scripture_sources and sop_sources:
            return ConfidenceLevel.MEDIUM
        
        # Medium confidence if we have multiple scripture sources
        if len(scripture_sources) >= 2:
            return ConfidenceLevel.MEDIUM
        
        # Low confidence if only commentary or single low-confidence source
        if only_commentary := not scripture_sources and not sop_sources:
            return ConfidenceLevel.LOW
        
        # Medium for mixed sources
        if scripture_sources or sop_sources:
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.UNCERTAIN
    
    def _generate_caveats(self,
                         scripture_sources: List[SourceCitation],
                         sop_sources: List[SourceCitation],
                         commentary_sources: List[SourceCitation],
                         overall_confidence: ConfidenceLevel) -> List[str]:
        """Generate appropriate caveats based on sources"""
        caveats = []
        
        # Low/uncertain confidence caveats
        if overall_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
            caveats.append("This interpretation could be wrong")
        
        # No scripture sources
        if not scripture_sources:
            caveats.append("This response lacks direct scriptural support")
        
        # Only commentary sources
        if commentary_sources and not scripture_sources and not sop_sources:
            caveats.append("This is based on human commentary, not inspired sources")
        
        # Mixed interpretive content
        if commentary_sources and overall_confidence <= ConfidenceLevel.MEDIUM:
            caveats.append("Multiple interpretive perspectives exist on this topic")
        
        return caveats
    
    def _extract_cross_references(self, search_results: List[Any]) -> List[str]:
        """Extract OSIS IDs for cross-referencing"""
        cross_refs = []
        
        for result in search_results:
            metadata = result.get('metadata', {})
            if osis_id := metadata.get('osis_id'):
                cross_refs.append(osis_id)
        
        return list(set(cross_refs))  # Remove duplicates
    
    def format_response_text(self, typed_response: TypedResponse) -> str:
        """Format typed response into readable text with proper humility"""
        sections = []
        
        # Scripture section
        if typed_response.scripture_sources:
            scripture_text = self._format_scripture_section(typed_response.scripture_sources)
            sections.append(scripture_text)
        
        # Spirit of Prophecy section
        if typed_response.sop_sources:
            sop_text = self._format_sop_section(typed_response.sop_sources)
            sections.append(sop_text)
        
        # Commentary section
        if typed_response.commentary_sources:
            commentary_text = self._format_commentary_section(typed_response.commentary_sources)
            sections.append(commentary_text)
        
        # Analysis section
        if typed_response.analysis:
            analysis_text = f"\n**TinyOwl Analysis**: {typed_response.analysis}"
            sections.append(analysis_text)
        
        # Caveats section
        if typed_response.caveats:
            caveats_text = "\n**Important Notes**:\n" + "\n".join(f"- {caveat}" for caveat in typed_response.caveats)
            sections.append(caveats_text)
        
        return "\n\n".join(sections)
    
    def _format_scripture_section(self, sources: List[SourceCitation]) -> str:
        """Format scripture sources with appropriate language"""
        if not sources:
            return ""
        
        text = "**Scripture states**:\n"
        for source in sources:
            ref = self._format_reference(source)
            text += f"- {ref}: \"{source.quote[:200]}{'...' if len(source.quote) > 200 else ''}\"\n"
        
        return text
    
    def _format_sop_section(self, sources: List[SourceCitation]) -> str:
        """Format Spirit of Prophecy sources"""
        if not sources:
            return ""
        
        text = "**Ellen White suggests**:\n"
        for source in sources:
            work = source.source_info.get('work', 'Unknown work')
            text += f"- {work}: \"{source.quote[:200]}{'...' if len(source.quote) > 200 else ''}\"\n"
        
        return text
    
    def _format_commentary_section(self, sources: List[SourceCitation]) -> str:
        """Format commentary sources"""
        if not sources:
            return ""
        
        text = "**Commentary perspective**:\n"
        for source in sources:
            author = source.source_info.get('author', 'Unknown author')
            text += f"- {author} argues: \"{source.quote[:200]}{'...' if len(source.quote) > 200 else ''}\"\n"
        
        return text
    
    def _format_reference(self, source: SourceCitation) -> str:
        """Format biblical reference"""
        if source.osis_id:
            # Convert OSIS ID to readable format
            parts = source.osis_id.split('.')
            if len(parts) == 3:
                book_id, chapter, verse = parts
                book_name = source.source_info.get('book', book_id)
                return f"{book_name} {int(chapter)}:{int(verse)}"
        
        return f"{source.source_info.get('book', '')} {source.source_info.get('chapter', '')}:{source.source_info.get('verses', '')}"
    
    def to_json(self, typed_response: TypedResponse) -> str:
        """Convert typed response to JSON for API/storage"""
        # Convert dataclass to dict, handling enums
        response_dict = asdict(typed_response)
        
        # Convert enums to strings
        for source_list in ['scripture_sources', 'sop_sources', 'commentary_sources']:
            for source in response_dict[source_list]:
                source['authority_level'] = source['authority_level'].value
                source['confidence'] = source['confidence'].value
        
        response_dict['overall_confidence'] = response_dict['overall_confidence'].value
        
        return json.dumps(response_dict, indent=2)


def test_humble_response():
    """Test the humble response system"""
    generator = HumbleResponseGenerator()
    
    # Mock search results
    mock_results = [
        {
            'id': 'kjv_john_03_016',
            'content': 'For God so loved the world, that he gave his only begotten Son...',
            'score': 0.95,
            'metadata': {
                'type': 'scripture',
                'source_id': 'bible_kjv',
                'book_name': 'John',
                'chapter_number': 3,
                'verse_numbers': '16',
                'osis_id': 'John.03.016'
            }
        },
        {
            'id': 'da_salvation_chapter',
            'content': 'The plan of salvation was laid before the foundation of the world...',
            'score': 0.82,
            'metadata': {
                'type': 'sop',
                'source_id': 'coa_desire_of_ages',
                'author': 'Ellen G. White',
                'title': 'The Desire of Ages'
            }
        }
    ]
    
    response = generator.create_typed_response(
        query="What is God's love?",
        search_results=mock_results,
        ai_analysis="God's love is demonstrated through the gift of salvation."
    )
    
    formatted = generator.format_response_text(response)
    print("Formatted Response:")
    print(formatted)
    
    print("\nJSON Response:")
    print(generator.to_json(response))


if __name__ == "__main__":
    test_humble_response()