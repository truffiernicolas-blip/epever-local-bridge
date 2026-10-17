"""Connexions courtes et séquentielles ; aucune redirection HTTP."""
import asyncio
import errno


async def inspect_port(host, port, timeout, http=False):
    writer = None
    result = {"port": port, "transport": "tcp", "state": "unknown",
              "protocol": "unknown", "evidence": []}
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
        result["state"] = "open"
        if http:
            writer.write((f"HEAD / HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\n\r\n").encode("ascii"))
            await asyncio.wait_for(writer.drain(), timeout)
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout)
            # Ne stocker ni corps HTTP, ni cookies, ni bannières arbitraires.
            if data.startswith(b"HTTP/1."):
                line = data.split(b"\r\n", 1)[0].split()
                if len(line) >= 2 and line[1].isdigit():
                    result["protocol"] = "http"
                    result["evidence"].append({"http_status": int(line[1])})
            elif data:
                result["evidence"].append({"unsolicited_bytes": len(data)})
        except asyncio.TimeoutError:
            result["evidence"].append("no_response_before_timeout")
    except ConnectionRefusedError:
        result["state"] = "closed"
    except asyncio.TimeoutError:
        result["state"] = "timeout_or_filtered"
    except OSError as exc:
        result["state"] = "closed" if exc.errno == errno.ECONNREFUSED else "network_error"
        result["error_code"] = exc.errno
    finally:
        if writer:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout)
            except (OSError, asyncio.TimeoutError):
                pass
    return result
