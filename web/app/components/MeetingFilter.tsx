import { useEffect, useState } from "react";
import { getCouncilDates } from "~/lib/search-api";

function formatDate(dateString: string) {
    const options: Intl.DateTimeFormatOptions = { year: "numeric", month: "2-digit", day: "2-digit" };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

export function MeetingFilter({dateFrom, dateTo}: {dateFrom: string | null, dateTo: string | null}) {
    const [selectedMeeting, setSelectedMeeting] = useState('');
    const [availableMeetings, setAvailableMeetings] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const loadDates = async () => {
            const outcome = await getCouncilDates(dateFrom, dateTo);
            if (!outcome.error) {
                setAvailableMeetings(outcome.dates);
            } else {
                setError(outcome.error);
            }
        
            setLoading(false);
        };
        loadDates();
    }, [dateFrom, dateTo]);

    return (loading ? <p>Lade...</p> : error ? <p>{error}</p> : <div><label
        htmlFor="meeting-filter">
        Sitzungsdatum
    </label>
        <select
            id="meeting-filter"
            name="meeting-filter"
            className="w-full rounded-lg border border-emerald-300 bg-white px-3 py-2 text-base text-gray-900 shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-50"
            value={selectedMeeting}
            onChange={(e) => setSelectedMeeting(e.target.value)}>
            <option value="">Alle Sitzungen</option>
            {availableMeetings.map((meeting) => (
                <option key={meeting} value={meeting}>
                    {formatDate(meeting)}
                </option>
            ))}
        </select>
    </div>);
}