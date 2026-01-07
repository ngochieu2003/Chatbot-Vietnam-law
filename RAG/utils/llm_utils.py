#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Utilities
Helper functions để tích hợp với các LLM providers
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def format_prompt(query: str, context: str) -> str:
    """
    Format prompt cho LLM
    
    Args:
        query: Câu hỏi của người dùng
        context: Context từ các chunks tìm được
        
    Returns:
        Prompt đã được format
    """
    prompt = f"""Bạn là trợ lý pháp luật chuyên nghiệp. Nhiệm vụ của bạn là trả lời câu hỏi về pháp luật Việt Nam dựa trên các điều luật được cung cấp.

Hướng dẫn:
- Trả lời chính xác, rõ ràng và dễ hiểu
- Chỉ dựa vào thông tin trong các điều luật được cung cấp
- Nếu không tìm thấy thông tin, hãy nói rõ "Tôi không tìm thấy thông tin về vấn đề này trong các điều luật được cung cấp"
- Luôn trích dẫn số điều luật khi trả lời
- Trả lời bằng tiếng Việt

Các điều luật liên quan:
{context}

Câu hỏi: {query}

Trả lời:"""
    
    return prompt


def generate_response_openai(
    prompt: str,
    model: str = 'gpt-3.5-turbo',
    temperature: float = 0.7,
    max_tokens: int = 500,
    api_key: Optional[str] = None
) -> str:
    """
    Generate response từ OpenAI GPT
    
    Args:
        prompt: Prompt đã được format
        model: Tên model (gpt-3.5-turbo, gpt-4, etc.)
        temperature: Temperature (0.0-1.0)
        max_tokens: Số tokens tối đa
        api_key: OpenAI API key (nếu không có trong .env)
        
    Returns:
        Generated response
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Cần cài đặt openai: pip install openai")
    
    # Lấy API key
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "Chưa có OpenAI API key! "
            "Đặt OPENAI_API_KEY trong file .env hoặc truyền vào function."
        )
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý pháp luật chuyên nghiệp."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Lỗi khi tạo response: {str(e)}"


def generate_response_ollama(
    prompt: str,
    model: str = 'llama2',
    temperature: float = 0.7,
    base_url: str = 'http://localhost:11434'
) -> str:
    """
    Generate response từ Local LLM (Ollama)
    
    Args:
        prompt: Prompt đã được format
        model: Tên model trong Ollama
        temperature: Temperature (0.0-1.0)
        base_url: URL của Ollama server
        
    Returns:
        Generated response
    """
    try:
        import requests
    except ImportError:
        raise ImportError("Cần cài đặt requests: pip install requests")
    
    try:
        # Kiểm tra Ollama có chạy không
        health_check = requests.get(f"{base_url}/api/tags", timeout=5)
        health_check.raise_for_status()
    except requests.exceptions.RequestException:
        return (
            f"❌ Không thể kết nối với Ollama tại {base_url}\n"
            f"   Hãy đảm bảo Ollama đang chạy:\n"
            f"   1. Cài đặt Ollama: https://ollama.ai\n"
            f"   2. Tải model: ollama pull {model}\n"
            f"   3. Khởi động Ollama server"
        )
    
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 500  # Giới hạn số tokens
                }
            },
            timeout=120  # Tăng timeout cho model lớn
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "response" in result:
            return result["response"].strip()
        else:
            return f"Lỗi: Response không hợp lệ từ Ollama: {result}"
    
    except requests.exceptions.Timeout:
        return "Lỗi: Timeout khi chờ response từ Ollama. Model có thể quá lớn hoặc chậm."
    except requests.exceptions.RequestException as e:
        return f"Lỗi khi kết nối với Ollama: {str(e)}"
    except KeyError as e:
        return f"Lỗi: Không nhận được response từ Ollama: {str(e)}"


def generate_response_claude(
    prompt: str,
    model: str = 'claude-3-sonnet-20240229',
    temperature: float = 0.7,
    max_tokens: int = 500,
    api_key: Optional[str] = None
) -> str:
    """
    Generate response từ Anthropic Claude
    
    Args:
        prompt: Prompt đã được format
        model: Tên model Claude
        temperature: Temperature (0.0-1.0)
        max_tokens: Số tokens tối đa
        api_key: Anthropic API key
        
    Returns:
        Generated response
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError("Cần cài đặt anthropic: pip install anthropic")
    
    # Lấy API key
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "Chưa có Anthropic API key! "
            "Đặt ANTHROPIC_API_KEY trong file .env hoặc truyền vào function."
        )
    
    client = Anthropic(api_key=api_key)
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text.strip()
    
    except Exception as e:
        return f"Lỗi khi tạo response: {str(e)}"


def generate_response_gemini(
    prompt: str,
    model: str = 'gemini-pro',
    temperature: float = 0.7,
    max_tokens: int = 500,
    api_key: Optional[str] = None
) -> str:
    """
    Generate response từ Google Gemini
    
    Args:
        prompt: Prompt đã được format
        model: Tên model Gemini (ví dụ: 'gemini-pro', 'gemini-1.5-flash')
        temperature: Temperature (0.0-1.0)
        max_tokens: Số tokens tối đa
        api_key: Gemini API key (GEMINI_API_KEY hoặc GOOGLE_API_KEY)
        
    Returns:
        Generated response
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Cần cài đặt google-generativeai: pip install google-generativeai")
    
    api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError(
            "Chưa có Gemini API key! "
            "Đặt GEMINI_API_KEY hoặc GOOGLE_API_KEY trong file .env hoặc truyền vào function."
        )
    
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    
    try:
        model_client = genai.GenerativeModel(model)
        response = model_client.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Primary accessor
        try:
            text = response.text
            if text:
                text = text.strip()
                # Detect if any candidate indicates truncation (MAX_TOKENS) and return an error-like
                # string so callers (RAG retry logic) can detect and retry with larger max_tokens.
                candidates = getattr(response, 'candidates', []) or []
                truncation_detected = False
                for cand in candidates:
                    try:
                        fr = getattr(cand, 'finish_reason', None)
                    except Exception:
                        fr = None
                    if fr is not None:
                        s = str(fr).lower()
                        if ('max' in s and 'token' in s) or 'max_tokens' in s or 'max_output' in s:
                            truncation_detected = True
                            break

                if truncation_detected:
                    return f"Lỗi: MAX_TOKENS - response truncated. Partial: {text}"

                return text
        except Exception:
            # hasattr() and direct access both fail when finish_reason=2, skip to candidates parsing
            pass

        # Fallback: try to combine parts from candidates in multiple possible shapes
        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            # candidate.content may be an object with .parts or a dict/list structure
            content = getattr(candidate, 'content', None)
            if content is None and isinstance(candidate, dict):
                content = candidate.get('content')

            if content is None:
                # try to inspect as dict
                if isinstance(candidate, dict):
                    for elem in candidate.get('content', []) or []:
                        for part in elem.get('parts', []) or []:
                            if isinstance(part, dict):
                                t = part.get('text')
                                if t:
                                    parts.append(t)
                else:
                    # unknown shape, append repr for debugging
                    parts.append(repr(candidate))
                continue

            # If content has .parts
            if hasattr(content, 'parts'):
                for part in getattr(content, 'parts') or []:
                    t = getattr(part, 'text', None)
                    if t:
                        parts.append(t)
            else:
                # content might be a list/dict
                if isinstance(content, list):
                    for elem in content:
                        for part in (elem.get('parts', []) if isinstance(elem, dict) else []) or []:
                            t = part.get('text') if isinstance(part, dict) else None
                            if t:
                                parts.append(t)

        if parts:
            full_text = "\n".join(parts).strip()
            # Check candidates for truncation reason as well
            candidates = getattr(response, 'candidates', []) or []
            truncation_detected = False
            for cand in candidates:
                try:
                    fr = getattr(cand, 'finish_reason', None)
                except Exception:
                    fr = None
                if fr is not None:
                    s = str(fr).lower()
                    if ('max' in s and 'token' in s) or 'max_tokens' in s or 'max_output' in s:
                        truncation_detected = True
                        break

            if truncation_detected:
                return f"Lỗi: MAX_TOKENS - response truncated. Partial: {full_text}"

            return full_text

        # Build debug information to help diagnose unexpected response shapes
        # Important: do NOT call `hasattr(response, 'text')` or `getattr(response, 'text', None')`
        # directly because the SDK's quick-accessor may raise a ValueError when Parts are missing
        # (finish_reason == MAX_TOKENS). Instead, access in a guarded way.
        _text = None
        try:
            _text = response.text
        except Exception:
            _text = None
        debug = {
            'response_repr': repr(response),
            'has_text': _text is not None,
            'text': _text,
            'candidates': []
        }
        for candidate in getattr(response, 'candidates', []) or []:
            cand_info = {}
            try:
                cand_info['finish_reason'] = getattr(candidate, 'finish_reason', None)
            except Exception:
                cand_info['finish_reason'] = None

            try:
                content = getattr(candidate, 'content')
            except Exception:
                content = None

            parts_list = []
            if content is not None:
                if hasattr(content, 'parts'):
                    for part in getattr(content, 'parts') or []:
                        try:
                            parts_list.append(getattr(part, 'text', None))
                        except Exception:
                            parts_list.append(None)
                elif isinstance(content, list):
                    for elem in content:
                        for part in (elem.get('parts', []) if isinstance(elem, dict) else []) or []:
                            parts_list.append(part.get('text'))
                else:
                    # unknown content shape; include repr for debugging
                    parts_list.append(repr(content))
            else:
                cand_info['raw'] = repr(candidate)

            cand_info['parts'] = parts_list
            debug['candidates'].append(cand_info)

        return f"Lỗi khi tạo response với Gemini: response structure unexpected. Debug: {debug}"
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return f"Lỗi khi tạo response với Gemini: {str(e)}\nTraceback:\n{tb}"


def list_gemini_models(api_key: Optional[str] = None):
    """
    List available Gemini/Google GenAI models.

    Trả về danh sách tên model (list of str) hoặc raise Exception nếu không thể lấy.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Cần cài đặt google-generativeai: pip install google-generativeai")

    api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError(
            "Chưa có Gemini API key! Đặt GEMINI_API_KEY hoặc GOOGLE_API_KEY trong file .env hoặc truyền vào function."
        )

    genai.configure(api_key=api_key)

    try:
        # Try a few possible list methods depending on SDK version
        models = None
        if hasattr(genai, 'list_models'):
            models = genai.list_models()
        elif hasattr(genai, 'Models') and hasattr(genai.Models, 'list'):
            models = genai.Models.list()
        elif hasattr(genai, 'models') and hasattr(genai.models, 'list'):
            models = genai.models.list()
        else:
            # Fallback: try calling a generic endpoint via genai
            try:
                models = genai.get_models()
            except Exception:
                raise RuntimeError('Không thể tìm hàm list models trong google.generativeai (SDK khác version)')

        # Normalize models to list of names
        result = []
        if isinstance(models, dict) and 'models' in models:
            items = models['models']
        else:
            items = models

        for m in items or []:
            if hasattr(m, 'name'):
                result.append(m.name)
            elif isinstance(m, dict) and 'name' in m:
                result.append(m['name'])
            else:
                result.append(str(m))

        return result

    except Exception as e:
        raise Exception(f"Lỗi khi lấy danh sách models: {e}")


def check_ollama_available(base_url: str = 'http://localhost:11434') -> bool:
    """
    Kiểm tra Ollama có sẵn sàng không
    
    Args:
        base_url: URL của Ollama server
        
    Returns:
        True nếu Ollama sẵn sàng, False nếu không
    """
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return True
    except:
        return False


def generate_response_auto(
    prompt: str,
    llm_provider: str = 'auto',
    llm_model: str = 'gpt-3.5-turbo',
    temperature: float = 0.7,
    max_tokens: int = 500,
    ollama_base_url: str = 'http://localhost:11434',
    api_key: Optional[str] = None
) -> str:
    """
    Generate response với auto-detection và fallback
    
    Thứ tự ưu tiên:
    1. Nếu llm_provider='auto': Tự động chọn (Ollama > OpenAI > Gemini > Claude)
    2. Nếu llm_provider='ollama': Dùng Ollama, fallback sang OpenAI nếu lỗi
    3. Nếu llm_provider='openai': Dùng OpenAI
    4. Nếu llm_provider='gemini': Dùng Google Gemini
    5. Nếu llm_provider='claude': Dùng Claude
    
    Args:
        prompt: Prompt đã được format
        llm_provider: Provider ('auto', 'ollama', 'openai', 'gemini', 'claude')
        llm_model: Tên model (tùy theo provider)
        temperature: Temperature (0.0-1.0)
        max_tokens: Số tokens tối đa
        ollama_base_url: URL của Ollama server
        api_key: API key (cho OpenAI hoặc Claude)
        
    Returns:
        Generated response
    """
    # Auto-detection
    if llm_provider == 'auto':
        # Thử Ollama trước (miễn phí)
        if check_ollama_available(ollama_base_url):
            print("🤖 Sử dụng Ollama (Local LLM)")
            try:
                # Xác định model Ollama từ llm_model
                ollama_model = llm_model if llm_model in ['llama2', 'mistral', 'phi', 'codellama'] else 'llama2'
                return generate_response_ollama(
                    prompt=prompt,
                    model=ollama_model,
                    temperature=temperature,
                    base_url=ollama_base_url
                )
            except Exception as e:
                print(f"⚠️  Ollama lỗi: {e}")
                pass
        
        # Fallback sang OpenAI
        if os.getenv('OPENAI_API_KEY') or api_key:
            print("🤖 Sử dụng OpenAI (Fallback)")
            return generate_response_openai(
                prompt=prompt,
                model=llm_model if 'gpt' in llm_model.lower() else 'gpt-3.5-turbo',
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        
        # Fallback sang Gemini
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or api_key:
            print("🤖 Sử dụng Gemini (Fallback)")
            return generate_response_gemini(
                prompt=prompt,
                model=llm_model if 'gemini' in llm_model.lower() else 'gemini-pro',
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        
        # Fallback sang Claude
        if os.getenv('ANTHROPIC_API_KEY') or api_key:
            print("🤖 Sử dụng Claude (Fallback)")
            return generate_response_claude(
                prompt=prompt,
                model=llm_model if 'claude' in llm_model.lower() else 'claude-3-sonnet-20240229',
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        
        raise ValueError(
            "Không tìm thấy LLM provider nào! "
            "Hãy cài đặt Ollama hoặc cung cấp API key cho OpenAI/Gemini/Claude."
        )
    
    # Explicit provider
    if llm_provider == 'ollama':
        try:
            return generate_response_ollama(
                prompt=prompt,
                model=llm_model,
                temperature=temperature,
                base_url=ollama_base_url
            )
        except Exception as e:
            print(f"⚠️  Ollama không khả dụng: {e}")
            print("🔄 Đang fallback sang OpenAI...")
            if os.getenv('OPENAI_API_KEY') or api_key:
                return generate_response_openai(
                    prompt=prompt,
                    model='gpt-3.5-turbo',
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key
                )
            raise
    
    elif llm_provider == 'openai':
        return generate_response_openai(
            prompt=prompt,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    elif llm_provider == 'gemini':
        return generate_response_gemini(
            prompt=prompt,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    elif llm_provider == 'claude':
        return generate_response_claude(
            prompt=prompt,
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    else:
        raise ValueError(f"LLM provider không hợp lệ: {llm_provider}. Chọn 'auto', 'ollama', 'openai', 'gemini', hoặc 'claude'.")

