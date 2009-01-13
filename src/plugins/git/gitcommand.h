/***************************************************************************
**
** This file is part of Qt Creator
**
** Copyright (c) 2008-2009 Nokia Corporation and/or its subsidiary(-ies).
**
** Contact:  Qt Software Information (qt-info@nokia.com)
**
**
** Non-Open Source Usage
**
** Licensees may use this file in accordance with the Qt Beta Version
** License Agreement, Agreement version 2.2 provided with the Software or,
** alternatively, in accordance with the terms contained in a written
** agreement between you and Nokia.
**
** GNU General Public License Usage
**
** Alternatively, this file may be used under the terms of the GNU General
** Public License versions 2.0 or 3.0 as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL included in the packaging
** of this file.  Please review the following information to ensure GNU
** General Public Licensing requirements will be met:
**
** http://www.fsf.org/licensing/licenses/info/GPLv2.html and
** http://www.gnu.org/copyleft/gpl.html.
**
** In addition, as a special exception, Nokia gives you certain additional
** rights. These rights are described in the Nokia Qt GPL Exception
** version 1.3, included in the file GPL_EXCEPTION.txt in this package.
**
***************************************************************************/

#ifndef GITCOMMAND_H
#define GITCOMMAND_H

#include <projectexplorer/environment.h>

#include <QtCore/QObject>

namespace Git {
namespace Internal {

class GitCommand : public QObject
{
    Q_OBJECT
public:
    explicit GitCommand(const QString &workingDirectory,
                        ProjectExplorer::Environment &environment);


    void addJob(const QStringList &arguments);
    void execute();

private:
    void run();

Q_SIGNALS:
    void outputData(const QByteArray&);
    void errorText(const QString&);

private:
    struct Job {
        explicit Job(const QStringList &a);

        QStringList arguments;
    };

    QStringList environment() const;

    const QString m_workingDirectory;
    const QStringList m_environment;

    QList<Job> m_jobs;
};

} // namespace Internal
} // namespace Git
#endif // GITCOMMAND_H
